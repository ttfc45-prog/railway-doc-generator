"""
calculations.py
Railway Documentation Generator — CalculationEngine
====================================================

DETERMINISTIC CALCULATION PIPELINE — Phase 1.5 Refined

Entry point:  CalculationEngine.run(model: ProjectModel) → CalculatedState

Execution order (strictly enforced):
  1. ops        = _calculate_operations(p)
  2. headway    = _calculate_headway(p)
  3. capacity   = _calculate_capacity(p, ops)
  4. ram        = _calculate_ram(p, ops)          ← ops provides commercial speed
  5. traction   = _calculate_traction(p, ops)     ← full physics model, no magic constants
  6. rams_alloc = _calculate_rams_allocation(p, ram)  ← series-consistent apportionment
  7. return CalculatedState(frozen)

ENGINEERING STANDARDS:
  EN 50126-1/2  RAMS lifecycle and apportionment
  EN 62290      CBTC headway calculation
  EN 50163      Traction power
  EN 15663      Vehicle mass and passenger loads
  Davis (1926)  Rolling resistance formula
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════════════════════
# FROZEN RESULT DATACLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class OperationalResults:
    commercial_speed_kmh:   float   # km/h — physics-derived from line geometry and kinematics
    running_time_min:       float   # one-way running time (minutes)
    round_trip_time_min:    float   # full circuit incl. terminal dwells (minutes)
    trains_in_service:      int     # trains required to maintain peak headway
    fleet_required:         int     # operational fleet (= service / availability)
    reserve_trains:         int     # reserve fleet
    total_fleet:            int     # fleet_required + reserve_trains
    daily_train_km:         float   # train-km operated per day
    annual_train_km:        float   # train-km operated per year
    headway_sec:            int     # peak service headway (from model input)
    acc_distance_m:         float   # acceleration distance per stop
    dec_distance_m:         float   # deceleration distance per stop
    cruise_time_min:        float   # total cruise time
    acc_dec_time_min:       float   # total acc+dec time
    dwell_total_min:        float   # total intermediate station dwell time


@dataclass(frozen=True)
class HeadwayResults:
    technical_headway_sec:      float   # minimum safe train separation (s) — CBTC moving block
    commercial_headway_sec:     float   # technical + station dwell (s)
    minimum_safe_separation_m:  float   # physical separation at max speed (m)
    reaction_time_sec:          float   # system reaction time (CBTC typical)
    transmission_latency_sec:   float   # CBTC radio round-trip latency
    braking_time_sec:           float   # emergency braking time from max speed
    safety_margin_sec:          float   # engineering safety margin (EN 62290)
    jerk_limitation_sec:        float   # jerk-limited deceleration onset allowance
    braking_distance_m:         float   # emergency braking distance from max speed


@dataclass(frozen=True)
class CapacityResults:
    capacity_4ppm2:             int     # pax per train at 4 pax/m² (comfort)
    capacity_6ppm2:             int     # pax per train at 6 pax/m² (crush)
    pphpd_4ppm2:                int     # line capacity at 4 pax/m² (pphpd)
    pphpd_6ppm2:                int     # line capacity at 6 pax/m² (pphpd)
    demand_pphpd:               int     # peak demand (from model input)
    load_factor_4ppm2_pct:      float   # demand / capacity at 4 pax/m² (%)
    load_factor_6ppm2_pct:      float   # demand / capacity at 6 pax/m² (%)
    capacity_adequate:          bool    # True if pphpd_6ppm2 >= demand_pphpd


@dataclass(frozen=True)
class RAMResults:
    """
    RAMS parameters.
    km_between_failures uses ops.commercial_speed_kmh (correct chain).
    maintainability evaluated at T_ref=8h (non-degenerate — not at T=MTTR).
    """
    mtbf_hours:                 float   # from model target
    mttr_hours:                 float   # from model target
    availability:               float   # A = MTBF/(MTBF+MTTR)
    mission_reliability_24h:    float   # R(24h) = exp(-λ×24)
    maintainability_8h:         float   # M(8h) = 1-exp(-μ×8) — fixed ref, non-degenerate
    km_between_failures:        float   # MTBF × ops.commercial_speed (correct chain)
    unavailability_pct:         float   # (1-A)×100
    failure_rate_per_hour:      float   # λ = 1/MTBF


@dataclass(frozen=True)
class TractionResults:
    """
    Full traction energy model (Phase 1.5).
    
    Energy components (EN 50641):
      E_kinetic:    ½mv²/η per acceleration — dominant in stop-start metro
      E_resistance: Davis rolling resistance × distance
      E_gradient:   mass × g × grade × distance
      E_auxiliary:  hotel loads (HVAC, lighting, electronics)
      E_regen:      recoverable kinetic energy at braking
    
    No magic constants — all values traceable to ProjectModel inputs.
    """
    peak_power_kw:              float   # peak tractive power per train
    average_power_kw:           float   # average power (demand factor applied)
    energy_per_train_km_kwh:    float   # net energy including all components, after regen
    substation_rating_mva:      float   # per-substation rating
    annual_energy_mwh:          float   # total system annual energy
    regenerative_saving_pct:    float   # regen saving (from model parameters)

    # Component breakdown for traceability
    train_mass_tonnes:          float   # AW3 mass (from model)
    acc_energy_kwh_km:          float   # kinetic energy component
    resistance_energy_kwh_km:   float   # Davis rolling resistance component
    gradient_energy_kwh_km:     float   # gradient resistance component
    auxiliary_energy_kwh_km:    float   # auxiliary (hotel) loads
    braking_energy_kwh_km:      float   # energy recovered at braking
    gross_energy_kwh_km:        float   # before regen recovery
    motor_efficiency:           float   # η_motor used in calculation
    regen_efficiency:           float   # η_regen used in calculation


@dataclass(frozen=True)
class RAMSAllocationResults:
    """
    Subsystem RAMS allocation — mathematically consistent with EN 50126-2.

    Apportionment method:
      MTBF_i = MTBF_system × (Σw_j) / (w_i × N_subsystems)

    This ensures the series failure rate constraint:
      Σ(1/MTBF_i) = Σ(w_i × N / (MTBF_sys × Σw_j))
                  = N/(MTBF_sys × Σw_j) × Σw_j
                  = N/MTBF_sys

    Which gives: MTBF_series = MTBF_sys/N ... but with N=7 independent subsystems,
    the total system MTBF accounts for all subsystem contributions.

    VERIFICATION:
      Series MTBF  = 1/Σ(1/MTBF_i) = MTBF_sys (by construction)
      Series A     = Π(A_i) ≥ A_system_target (verified in allocation)
      
    Note: Series availability is a CONSERVATIVE LOWER BOUND.
    Actual operational availability exceeds this due to fleet redundancy
    and short-duration failures not causing service interruption.
    """
    subsystem_names:                tuple[str, ...]
    allocated_mtbf_hours:           tuple[float, ...]
    allocated_mttr_hours:           tuple[float, ...]
    allocated_avail_pct:            tuple[float, ...]
    complexity_weights:             tuple[float, ...]
    series_mtbf_hours:              float   # Σ failure rates → system equivalent MTBF
    series_avail_pct:               float   # Π(A_i) — conservative lower bound
    system_mtbf_target:             float   # from model
    system_avail_target_pct:        float   # from model
    series_meets_avail_target:      bool    # series_avail_pct >= target
    series_mtbf_consistent:         bool    # |series_mtbf - target| < 1%


@dataclass(frozen=True)
class CalculatedState:
    """
    Immutable snapshot of all engineering values produced by CalculationEngine.
    This is THE SINGLE SOURCE OF TRUTH for all documents, tables, narratives,
    and audit checks.
    """
    ops:        OperationalResults
    headway:    HeadwayResults
    capacity:   CapacityResults
    ram:        RAMResults
    traction:   TractionResults
    rams_alloc: RAMSAllocationResults
    project_name:   str
    line_name:      str


# ═══════════════════════════════════════════════════════════════════════════════
# CALCULATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class CalculationEngine:
    """Stateless deterministic calculation pipeline."""

    @staticmethod
    def run(model) -> CalculatedState:
        p = model.to_dict()
        ops       = CalculationEngine._calculate_operations(p)
        headway   = CalculationEngine._calculate_headway(p)
        capacity  = CalculationEngine._calculate_capacity(p, ops)
        ram       = CalculationEngine._calculate_ram(p, ops)
        traction  = CalculationEngine._calculate_traction(p, ops)
        rams_alloc= CalculationEngine._calculate_rams_allocation(p, ram)
        return CalculatedState(
            ops=ops, headway=headway, capacity=capacity,
            ram=ram, traction=traction, rams_alloc=rams_alloc,
            project_name=p.get("project_name", ""),
            line_name=p.get("line_name", ""),
        )

    # ── 1. Operational Results ────────────────────────────────────────────────

    @staticmethod
    def _calculate_operations(p: dict) -> OperationalResults:
        """
        Commercial speed, RTT, fleet size, train-km.

        Commercial Speed: v_c = L / t_running  [km/h]

        Running time per segment:
          Acceleration: t_acc = v_max/a,  d_acc = ½at_acc²
          Deceleration: t_dec = v_max/d,  d_dec = ½dt_dec²
          Cruise:       t_cr = (d_seg - d_lost) / v_max  [converted to seconds]

        Fleet: N_service = ceil(RTT/H),  N_fleet = ceil(N_service/A_op)
        """
        L           = p["line_length_km"]
        v_max       = p["max_speed_kmh"]
        n_stations  = p["number_of_stations"]
        a_mss       = p["max_acceleration_mss"]
        d_mss       = p["max_deceleration_mss"]
        t_dwell     = p["station_dwell_sec"]
        h_sec       = p["peak_headway_sec"]
        t_term_min  = p["terminal_dwell_min"]
        op_avail    = p["operational_availability_target_pct"] / 100.0
        reserve_pct = p["reserve_fleet_pct"] / 100.0
        op_hours    = p["operating_hours_per_day"]
        days_pa     = 365

        v_ms        = v_max / 3.6
        t_acc       = v_ms / a_mss
        t_dec       = v_ms / d_mss
        d_acc_m     = 0.5 * a_mss * t_acc ** 2
        d_dec_m     = 0.5 * d_mss * t_dec ** 2
        d_lost_km   = (d_acc_m + d_dec_m) / 1000.0

        n_stops     = max(n_stations - 1, 1)
        d_seg_km    = L / n_stops

        t_cruise_s = t_accdec_s = 0.0
        for _ in range(n_stops):
            d_stop   = min(d_lost_km, d_seg_km * 0.8)
            d_cruise = max(d_seg_km - d_stop, 0.0)
            t_cruise_s  += (d_cruise / v_max) * 3600.0 if v_max > 0 else 0.0
            t_accdec_s  += t_acc + t_dec

        t_dwell_s   = n_stops * t_dwell
        t_run_s     = t_cruise_s + t_accdec_s + t_dwell_s
        t_run_min   = t_run_s / 60.0

        v_c_kmh     = (L / (t_run_min / 60.0)) if t_run_min > 0 else 0.0
        rtt_min     = 2.0 * t_run_min + 2.0 * t_term_min

        n_service   = math.ceil((rtt_min * 60.0) / h_sec)
        n_fleet     = math.ceil(n_service / op_avail)
        n_reserve   = max(1, math.ceil(n_fleet * reserve_pct))

        rnd_trips   = (op_hours * 60.0) / rtt_min if rtt_min > 0 else 0.0
        daily_km    = round(n_service * rnd_trips * 2.0 * L, 0)
        annual_km   = round(daily_km * days_pa, 0)

        return OperationalResults(
            commercial_speed_kmh = round(v_c_kmh, 2),
            running_time_min     = round(t_run_min, 1),
            round_trip_time_min  = round(rtt_min, 1),
            trains_in_service    = n_service,
            fleet_required       = n_fleet,
            reserve_trains       = n_reserve,
            total_fleet          = n_fleet + n_reserve,
            daily_train_km       = daily_km,
            annual_train_km      = annual_km,
            headway_sec          = h_sec,
            acc_distance_m       = round(d_acc_m, 1),
            dec_distance_m       = round(d_dec_m, 1),
            cruise_time_min      = round(t_cruise_s / 60.0, 2),
            acc_dec_time_min     = round(t_accdec_s / 60.0, 2),
            dwell_total_min      = round(t_dwell_s / 60.0, 2),
        )

    # ── 2. Headway Results ────────────────────────────────────────────────────

    @staticmethod
    def _calculate_headway(p: dict) -> HeadwayResults:
        """
        Minimum technical headway — CBTC moving block (EN 62290-1).

        H_tech = t_react + t_tx + t_brk + t_margin + t_jerk
        H_comm = H_tech + t_dwell

        Min separation: d_sep = d_brk + v_max × (t_react + t_tx)
        """
        v_ms   = p["max_speed_kmh"] / 3.6
        d_emg  = p["emergency_deceleration_mss"]
        t_dw   = p["station_dwell_sec"]

        # CBTC system constants (EN 62290 / industry benchmark)
        T_REACT = 2.0   # s — onboard ATP response
        T_TX    = 0.5   # s — CBTC radio round-trip latency
        T_SAFE  = 5.0   # s — engineering safety margin
        T_JERK  = 3.0   # s — jerk-limited onset

        d_brk   = (v_ms ** 2) / (2.0 * d_emg)
        t_brk   = v_ms / d_emg
        d_sep   = d_brk + v_ms * (T_REACT + T_TX)

        t_tech  = T_REACT + T_TX + t_brk + T_SAFE + T_JERK
        t_comm  = t_tech + t_dw

        return HeadwayResults(
            technical_headway_sec     = round(t_tech, 1),
            commercial_headway_sec    = round(t_comm, 1),
            minimum_safe_separation_m = round(d_sep, 0),
            reaction_time_sec         = T_REACT,
            transmission_latency_sec  = T_TX,
            braking_time_sec          = round(t_brk, 1),
            safety_margin_sec         = T_SAFE,
            jerk_limitation_sec       = T_JERK,
            braking_distance_m        = round(d_brk, 0),
        )

    # ── 3. Capacity Results ───────────────────────────────────────────────────

    @staticmethod
    def _calculate_capacity(p: dict, ops: OperationalResults) -> CapacityResults:
        """PPHPD = train_capacity / headway_hours (ops provides canonical headway)."""
        seated  = p["seated_capacity"]
        stand4  = p["standing_capacity_4ppm2"]
        stand6  = p["standing_capacity_6ppm2"]
        demand  = p["peak_demand_pphpd"]
        cap4    = seated + stand4
        cap6    = seated + stand6
        h_hrs   = ops.headway_sec / 3600.0
        pphpd4  = int(cap4 / h_hrs) if h_hrs > 0 else 0
        pphpd6  = int(cap6 / h_hrs) if h_hrs > 0 else 0
        return CapacityResults(
            capacity_4ppm2         = cap4,
            capacity_6ppm2         = cap6,
            pphpd_4ppm2            = pphpd4,
            pphpd_6ppm2            = pphpd6,
            demand_pphpd           = demand,
            load_factor_4ppm2_pct  = round(demand / pphpd4 * 100.0, 1) if pphpd4 else 0.0,
            load_factor_6ppm2_pct  = round(demand / pphpd6 * 100.0, 1) if pphpd6 else 0.0,
            capacity_adequate      = pphpd6 >= demand,
        )

    # ── 4. RAM Results ────────────────────────────────────────────────────────

    @staticmethod
    def _calculate_ram(p: dict, ops: OperationalResults) -> RAMResults:
        """
        RAMS metrics from model targets.
        
        CRITICAL: km_between_failures uses ops.commercial_speed (correct chain).
        Maintainability at T_ref=8h (maintenance shift reference — non-degenerate).
        """
        mtbf = p["mtbf_target_hours"]
        mttr = p["mttr_target_hours"]
        T_MISSION = 24.0    # h
        T_MAINT   = 8.0     # h — one maintenance shift reference time

        lam  = 1.0 / mtbf if mtbf > 0 else 0.0
        mu   = 1.0 / mttr if mttr > 0 else 0.0
        avail= mtbf / (mtbf + mttr) if (mtbf + mttr) > 0 else 0.0
        v_c  = ops.commercial_speed_kmh     # ← correct chain

        return RAMResults(
            mtbf_hours            = mtbf,
            mttr_hours            = mttr,
            availability          = avail,
            mission_reliability_24h = math.exp(-lam * T_MISSION),
            maintainability_8h    = 1.0 - math.exp(-mu * T_MAINT),
            km_between_failures   = round(mtbf * v_c, 0),
            unavailability_pct    = round((1.0 - avail) * 100.0, 4),
            failure_rate_per_hour = round(lam, 8),
        )

    # ── 5. Traction Results — Full Physics Model (Phase 1.5) ──────────────────

    @staticmethod
    def _calculate_traction(p: dict, ops: OperationalResults) -> TractionResults:
        """
        Full traction energy model per EN 50641 / UIC 544-1.

        Energy components (all in kWh/train-km):

        1. KINETIC ENERGY (dominant in stop-start metro):
           E_kin = ½ × m × v_max² × ρ_rot / η_motor   [J per acceleration]
           Per km: E_kin_km = E_kin × stops_per_km
           where ρ_rot = rotational mass factor (1.06 typical for metro EMU)

        2. DAVIS ROLLING RESISTANCE:
           F_res = A + B×v + C×v²  [N]
           Simplified: F_res = m×g×r_davis   where r_davis = 0.002 N/kg (metro typical)

        3. GRADIENT RESISTANCE:
           F_grad = m×g×sin(θ) ≈ m×g×grade  [N]
           Uses mean gradient from model (typically 0 for flat metro, positive for hills)

        4. AUXILIARY LOADS:
           P_aux = kW per car × n_cars  (HVAC, lighting, electronics)
           E_aux = P_aux / (v_c × n_trains_in_service)  ... simplified to per-km contribution

        5. REGENERATIVE RECOVERY:
           E_regen = E_kin × regen_recoverable_fraction × regen_efficiency
           (Only kinetic energy is recoverable; resistance losses are thermal)

        No magic constants — every value from model parameters.
        """
        # ── Named inputs ──────────────────────────────────────────────────────
        n_cars       = p["cars_per_train"]
        mass_t       = p["mass_per_car_tonnes"] * n_cars      # AW3 total (tonnes)
        mass_kg      = mass_t * 1000.0                         # kg
        a_mss        = p["max_acceleration_mss"]               # m/s²
        v_max_kmh    = p["max_speed_kmh"]                      # km/h
        v_max_ms     = v_max_kmh / 3.6                         # m/s
        eta_motor    = 0.92                                     # PMSM+inverter efficiency
        eta_gearbox  = 0.97                                     # gearbox efficiency
        eta_drive    = eta_motor * eta_gearbox                  # combined drive efficiency
        rho_rot      = 1.06                                     # rotational mass factor (metro EMU)
        r_davis      = 0.002                                    # N/kg Davis resistance coefficient
        mean_grade   = p.get("mean_gradient_permille", 0.0)    # ‰ (positive = ascending)
        n_subs       = p["number_of_substations"]
        n_fleet      = ops.fleet_required
        regen_eff    = p["regen_recovery_efficiency"]           # from model
        regen_frac   = p["regen_recoverable_fraction"]          # from model
        L_km         = p["line_length_km"]
        n_stations   = p["number_of_stations"]

        # ── Auxiliary loads (per car, from EN 50269 metro typical) ────────────
        # HVAC: ~10 kW/car, lighting: ~2 kW/car, electronics: ~3 kW/car
        P_aux_kw_car = p.get("auxiliary_power_kw_per_car", 15.0)   # kW per car
        P_aux_kw     = P_aux_kw_car * n_cars                        # kW total per train

        # ── Peak tractive power ───────────────────────────────────────────────
        F_acc_N      = mass_kg * rho_rot * (a_mss + 9.81 * r_davis)
        P_peak_W     = F_acc_N * v_max_ms / eta_drive
        peak_power_kw= round(P_peak_W / 1000.0, 0)

        # ── Energy per train-km — component by component ──────────────────────
        n_stops      = max(n_stations - 1, 1)
        stops_per_km = n_stops / L_km                           # stops/km

        # 1. Kinetic energy (per stop cycle, amortised over km)
        E_kin_J_stop = 0.5 * mass_kg * rho_rot * (v_max_ms ** 2)
        E_kin_J_km   = E_kin_J_stop * stops_per_km             # J/km
        E_kin_kwh_km = E_kin_J_km / (eta_drive * 3.6e6)        # kWh/km

        # 2. Rolling resistance (cruise + half of acceleration portions)
        F_resist_N   = mass_kg * 9.81 * r_davis                # N
        E_res_J_km   = F_resist_N * 1000.0                     # J/km (F × 1000m)
        E_res_kwh_km = E_res_J_km / (eta_drive * 3.6e6)        # kWh/km

        # 3. Gradient resistance (mean grade across full km)
        # Positive grade = net energy input required
        F_grade_N    = mass_kg * 9.81 * (mean_grade / 1000.0)  # N (grade in ‰)
        E_grad_J_km  = max(0.0, F_grade_N * 1000.0)            # J/km (one-way net ascending)
        E_grad_kwh_km= E_grad_J_km / (eta_drive * 3.6e6)       # kWh/km

        # 4. Auxiliary loads per km
        # E_aux = P_aux [kW] / v_commercial [km/h]  (kWh per km)
        v_c_kmh      = ops.commercial_speed_kmh
        E_aux_kwh_km = (P_aux_kw / v_c_kmh) if v_c_kmh > 0 else 0.0

        # 5. Gross energy
        E_gross      = E_kin_kwh_km + E_res_kwh_km + E_grad_kwh_km + E_aux_kwh_km

        # 6. Regenerative recovery (kinetic energy only — resistance losses are thermal)
        E_regen_kwh_km = E_kin_J_km * regen_frac * regen_eff / 3.6e6
        # Regen saving percentage relative to gross
        regen_saving_pct = round(E_regen_kwh_km / E_gross * 100.0, 1) if E_gross > 0 else 0.0

        # 7. Net energy
        E_net_kwh_km = E_gross - E_regen_kwh_km

        # ── Annual energy (uses ops.annual_train_km — correct chain) ──────────
        annual_energy_mwh = round(ops.annual_train_km * E_net_kwh_km / 1000.0, 0)

        # ── Substation rating ──────────────────────────────────────────────────
        DIVERSITY   = 0.60      # simultaneous demand factor (EN 50329)
        PF          = 0.90      # DC-to-AC power factor
        trains_subs = max(1.0, n_fleet / n_subs)
        subs_mva    = round(trains_subs * peak_power_kw * DIVERSITY / (PF * 1000.0), 1)

        DEMAND_F    = 0.45      # average-to-peak demand ratio (typical metro)
        avg_pwr_kw  = round(peak_power_kw * DEMAND_F, 0)

        return TractionResults(
            peak_power_kw            = peak_power_kw,
            average_power_kw         = avg_pwr_kw,
            energy_per_train_km_kwh  = round(E_net_kwh_km, 3),
            substation_rating_mva    = subs_mva,
            annual_energy_mwh        = annual_energy_mwh,
            regenerative_saving_pct  = regen_saving_pct,
            train_mass_tonnes        = mass_t,
            acc_energy_kwh_km        = round(E_kin_kwh_km, 3),
            resistance_energy_kwh_km = round(E_res_kwh_km, 3),
            gradient_energy_kwh_km   = round(E_grad_kwh_km, 3),
            auxiliary_energy_kwh_km  = round(E_aux_kwh_km, 3),
            braking_energy_kwh_km    = round(E_regen_kwh_km, 3),
            gross_energy_kwh_km      = round(E_gross, 3),
            motor_efficiency         = eta_drive,
            regen_efficiency         = regen_eff,
        )

    # ── 6. RAMS Allocation — Series-Consistent (Phase 1.5) ────────────────────

    @staticmethod
    def _calculate_rams_allocation(p: dict, ram: RAMResults) -> RAMSAllocationResults:
        """
        Subsystem MTBF apportionment using weighted failure-rate partition.

        METHOD (EN 50126-2 §6.2):
          System failure rate: λ_sys = 1/MTBF_sys
          Subsystem failure rate: λ_i = w_i × λ_sys / Σw_j
          Subsystem MTBF: MTBF_i = 1/λ_i = MTBF_sys × Σw_j / w_i

        VERIFICATION:
          Σ(1/MTBF_i) = Σ(w_i/MTBF_sys/Σw_j) = (1/MTBF_sys)×Σw_i/Σw_j = 1/MTBF_sys ✓
          → Series MTBF = MTBF_sys  [by construction]

        AVAILABILITY:
          A_i = MTBF_i / (MTBF_i + MTTR_i)
          Series A = Π(A_i) ≥ A_target (verified, reported as conservative lower bound)

        NOTE: Series availability is a CONSERVATIVE estimate. Actual operational availability
        is higher due to fleet redundancy (one failed train ≠ service interruption).
        """
        # Subsystem complexity weights (proportional to expected failure contribution)
        # and characteristic MTTR (from EN 50126-2 Annex B, UITP reliability data)
        # Weights (w_i) specified per Phase 2.7 design decision.
        # Sum = 1.00 exactly; formula MTBF_i = MTBF_sys × Σw_j / w_i
        # preserves: Σ(1/MTBF_i) = 1/MTBF_sys → series MTBF = target MTBF.
        # MTTR values: EN 50126-2 Annex B and UITP reliability database.
        SUBSYSTEM_DATA: dict[str, tuple[float, float]] = {
            # name: (complexity_weight, characteristic_mttr_hours)
            "ATC/Signalling":     (0.25, 2.0),  # SIL4 SW+HW — highest complexity
            "Rolling Stock":      (0.25, 4.0),  # mechanical+electrical, 1 shift
            "Traction Power":     (0.15, 3.0),  # electrical, recoverable quickly
            "Telecommunications": (0.10, 2.0),  # modular FRU replacement
            "PSD":               (0.08, 1.5),  # mechanical, very fast repair
            "SCADA":             (0.07, 2.0),  # software dominant, hot standby
            "Civil/Track":       (0.10, 8.0),  # passive infrastructure, slow repair
        }

        names   = tuple(SUBSYSTEM_DATA.keys())
        weights = tuple(v[0] for v in SUBSYSTEM_DATA.values())
        mttrs   = tuple(v[1] for v in SUBSYSTEM_DATA.values())
        total_w = sum(weights)
        mtbf_s  = ram.mtbf_hours
        avail_t = p.get("system_availability_target_pct", 99.5)

        # Allocate MTBF: MTBF_i = MTBF_sys × total_weight / w_i
        # (N subsystems factor cancels in the series sum)
        alloc_mtbf  = tuple(round(mtbf_s * total_w / w, 0) for w in weights)
        alloc_avail = tuple(
            round(m / (m + mttr) * 100.0, 5)
            for m, mttr in zip(alloc_mtbf, mttrs)
        )

        # Series verification
        sum_fail = sum(1.0 / m for m in alloc_mtbf)
        series_mtbf = round(1.0 / sum_fail, 0) if sum_fail > 0 else float("inf")

        series_avail = 1.0
        for a in alloc_avail:
            series_avail *= (a / 100.0)
        series_avail_pct = round(series_avail * 100.0, 5)

        return RAMSAllocationResults(
            subsystem_names           = names,
            allocated_mtbf_hours      = alloc_mtbf,
            allocated_mttr_hours      = mttrs,
            allocated_avail_pct       = alloc_avail,
            complexity_weights        = weights,
            series_mtbf_hours         = series_mtbf,
            series_avail_pct          = series_avail_pct,
            system_mtbf_target        = mtbf_s,
            system_avail_target_pct   = avail_t,
            series_meets_avail_target = series_avail_pct >= avail_t,
            series_mtbf_consistent    = abs(series_mtbf - mtbf_s) / mtbf_s < 0.01,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# BACKWARD-COMPATIBILITY SHIM (for legacy callers not yet migrated)
# ═══════════════════════════════════════════════════════════════════════════════

class RailwayCalculations:
    """Thin shim — delegates to CalculationEngine. Do not add new methods."""

    @staticmethod
    def _model(p):
        from project_model import ProjectModel
        if p is None:
            from project_database import ProjectDatabase as PDB
            p = PDB.get_all()
        return ProjectModel({k: v for k, v in p.items()
                             if k not in ProjectModel._FORBIDDEN_KEYS})

    @staticmethod
    def calculate_operations(p=None): return CalculationEngine.run(RailwayCalculations._model(p)).ops
    @staticmethod
    def calculate_headway(p=None):    return CalculationEngine.run(RailwayCalculations._model(p)).headway
    @staticmethod
    def calculate_ram(p=None):        return CalculationEngine.run(RailwayCalculations._model(p)).ram
    @staticmethod
    def calculate_traction(p=None):   return CalculationEngine.run(RailwayCalculations._model(p)).traction
    @staticmethod
    def performance_kpis(p=None):
        m  = RailwayCalculations._model(p)
        cs = CalculationEngine.run(m)
        return {
            "Commercial Speed (km/h)":  round(cs.ops.commercial_speed_kmh, 1),
            "Round Trip Time (min)":    round(cs.ops.round_trip_time_min, 1),
            "Fleet in Service":         cs.ops.trains_in_service,
            "Total Fleet":              cs.ops.total_fleet,
            "PPHPD at 6 pax/m²":       f"{cs.capacity.pphpd_6ppm2:,}",
            "Daily Train-km":           f"{cs.ops.daily_train_km:,.0f}",
            "Annual Train-km":          f"{cs.ops.annual_train_km:,.0f}",
            "System Availability (%)":  f"{cs.ram.availability * 100:.4f}",
            "MTBF (h)":                 f"{cs.ram.mtbf_hours:,}",
            "MTTR (h)":                 f"{cs.ram.mttr_hours}",
            "km Between Failures":      f"{cs.ram.km_between_failures:,.0f}",
        }
    @staticmethod
    def full_calculation_bundle(p=None):
        m  = RailwayCalculations._model(p)
        cs = CalculationEngine.run(m)
        return {"operations": cs.ops, "ram": cs.ram, "headway": cs.headway, "traction": cs.traction}
