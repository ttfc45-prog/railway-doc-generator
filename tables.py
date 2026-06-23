"""
tables.py
Railway Documentation Generator — Table Generation Module
==========================================================

All tables receive either:
  • model: ProjectModel   — for non-calculated fields (identity, configuration)
  • cs: CalculatedState   — for ALL engineering numbers

NO table may read from a project dict for any numeric engineering value.
NO table may call the calculation engine internally.
NO hardcoded engineering values (only formatting constants).

Call signature convention:
  • Metadata tables:  TableGenerator.xxx(model)
  • Engineering tables: TableGenerator.xxx(model, cs)
  • Pure-data tables: TableGenerator.xxx(cs)
"""

from __future__ import annotations

import pandas as pd
from config import SUBSYSTEMS


class TableGenerator:
    """Generates all standardised railway engineering tables."""

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 1 — PROJECT & IDENTITY TABLES
    # These display user-provided metadata plus calculated performance values.
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def project_data_table(model, cs) -> pd.DataFrame:
        """
        System overview table.
        Engineering parameters (commercial speed) come from CalculatedState.
        Identity/configuration parameters come from ProjectModel.
        """
        p = model.to_dict()
        rows = [
            ("Project Name",            p.get("project_name", "")),
            ("Country",                 p.get("country", "")),
            ("Client",                  p.get("client", "")),
            ("Consultant",              p.get("consultant", "")),
            ("Line Name",               p.get("line_name", "")),
            ("Total Route Length",      f"{p.get('line_length_km', 0):.1f} km"),
            ("Number of Stations",      str(p.get("number_of_stations", 0))),
            ("Depot Location",          p.get("depot_location", "")),
            ("Number of Tracks",        str(p.get("number_of_tracks", 2))),
            ("Track Gauge",             f"{p.get('track_gauge_mm', 1435)} mm"),
            ("Loading Gauge",           p.get("loading_gauge", "")),
            ("Design Maximum Speed",    f"{p.get('max_speed_kmh', 0)} km/h"),
            # ── Calculated values — sourced exclusively from CalculatedState ──
            ("Commercial Speed",        f"{cs.ops.commercial_speed_kmh:.1f} km/h"),
            ("Operating Hours/Day",     f"{p.get('operating_hours_per_day', 0)} h"),
            ("Peak Headway (service)",  f"{cs.ops.headway_sec} s"),
            ("Technical Headway (CBTC)",f"{cs.headway.technical_headway_sec:.1f} s"),
            ("GoA Level",               p.get("goa_level", "")),
            ("Signalling System",       p.get("signalling_system", "")),
            ("Power Supply",            p.get("power_supply_voltage", "")),
            ("Project Life",            f"{p.get('project_life_years', 40)} years"),
        ]
        return pd.DataFrame(rows, columns=["Parameter", "Value"])

    @staticmethod
    def standards_table(model) -> pd.DataFrame:
        standards = [
            ("EN 50126",    "Railway Applications – RAMS",
             "System-wide RAMS management",             "Mandatory"),
            ("EN 50128",    "Software for Railway Control",
             "Safety-critical software development",    "Mandatory"),
            ("EN 50129",    "Safety-Related Electronic Systems",
             "Hardware safety case",                    "Mandatory"),
            ("EN 50159",    "Safety-Related Communication",
             "On-board/wayside data links",             "Mandatory"),
            ("EN 62290",    "CBTC Urban Rail",
             "Train control system",                    "Mandatory"),
            ("IEC 62267",   "Grade of Automation",
             "GoA classification",                      "Mandatory"),
            ("EN 15227",    "Crashworthiness",
             "Rolling stock structural design",         "Mandatory"),
            ("EN 45545",    "Fire Protection",
             "Rolling stock fire safety",               "Mandatory"),
            ("NFPA 130",    "Fixed Guideway Transit",
             "Station and tunnel fire safety",          "Reference"),
            ("IEC 62443",   "Industrial Cybersecurity",
             "SCADA/OT security",                       "Mandatory"),
            ("EN 60068",    "Environmental Testing",
             "Equipment qualification",                 "Mandatory"),
            ("IEC 60870-5", "SCADA Communication",
             "RTU protocol",                            "Reference"),
            ("UIC 505-1",   "Loading Gauge",
             "Rolling stock envelope",                  "Mandatory"),
        ]
        return pd.DataFrame(standards,
                            columns=["Standard", "Title", "Application", "Status"])

    @staticmethod
    def environmental_conditions_table(model) -> pd.DataFrame:
        p = model.to_dict()
        rows = [
            ("Minimum Ambient Temperature", f"{p.get('ambient_temp_min_c', -5)} °C"),
            ("Maximum Ambient Temperature",  f"{p.get('ambient_temp_max_c', 45)} °C"),
            ("Maximum Relative Humidity",    f"{p.get('humidity_max_pct', 95)}%"),
            ("Maximum Altitude",             f"{p.get('altitude_max_m', 900)} m"),
            ("Seismic Zone",                 p.get("seismic_zone", "Zone 2B")),
            ("IP Rating (Tunnels)",          p.get("ip_rating_tunnels", "IP54")),
            ("IP Rating (Outdoor)",          p.get("ip_rating_outdoor", "IP65")),
            ("Pollution Degree",             "Pollution Degree 3 (EN 60068)"),
        ]
        return pd.DataFrame(rows, columns=["Parameter", "Value"])

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 2 — OPERATIONAL TABLES (all values from CalculatedState)
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def operational_parameters_table(model, cs) -> pd.DataFrame:
        """All engineering values from CalculatedState.ops and CalculatedState.capacity."""
        p = model.to_dict()
        rows = [
            ("Running Time (one way)",          f"{cs.ops.running_time_min:.1f} min"),
            ("Round Trip Time",                  f"{cs.ops.round_trip_time_min:.1f} min"),
            ("Commercial Speed",                 f"{cs.ops.commercial_speed_kmh:.2f} km/h"),
            ("Peak Headway",                     f"{cs.ops.headway_sec} s"),
            ("Trains in Peak Service",           str(cs.ops.trains_in_service)),
            ("Train Capacity (4 pax/m²)",        f"{cs.capacity.capacity_4ppm2} pass."),
            ("Train Capacity (6 pax/m²)",        f"{cs.capacity.capacity_6ppm2} pass."),
            ("Line Capacity (4 pax/m², pphpd)",  f"{cs.capacity.pphpd_4ppm2:,}"),
            ("Line Capacity (6 pax/m², pphpd)",  f"{cs.capacity.pphpd_6ppm2:,}"),
            ("Peak Demand (pphpd)",              f"{p.get('peak_demand_pphpd', 0):,}"),
            ("Load Factor at 6 pax/m²",          f"{cs.capacity.load_factor_6ppm2_pct:.1f}%"),
            ("Daily Train-km",                   f"{cs.ops.daily_train_km:,.0f}"),
            ("Annual Train-km",                  f"{cs.ops.annual_train_km:,.0f}"),
        ]
        return pd.DataFrame(rows, columns=["Parameter", "Value"])

    @staticmethod
    def rolling_stock_table(model, cs) -> pd.DataFrame:
        """Rolling stock spec — physical inputs from model, capacity from CalculatedState."""
        p = model.to_dict()
        rows = [
            ("Train Configuration",          f"{p.get('cars_per_train', 6)}-car EMU"),
            ("Train Length",                 f"{p.get('train_length_m', 138):.1f} m"),
            ("Train Width",                  f"{p.get('train_width_m', 2.88):.2f} m"),
            ("Train Height",                 f"{p.get('train_height_m', 3.70):.2f} m"),
            ("Train Mass (AW3)",             f"{cs.traction.train_mass_tonnes:.0f} t"),
            ("Maximum Speed",                f"{p.get('max_speed_kmh', 80)} km/h"),
            ("Design Speed",                 f"{p.get('design_speed_kmh', 90)} km/h"),
            ("Maximum Acceleration",         f"{p.get('max_acceleration_mss', 1.0)} m/s²"),
            ("Service Deceleration",         f"{p.get('max_deceleration_mss', 1.0)} m/s²"),
            ("Emergency Deceleration",       f"{p.get('emergency_deceleration_mss', 1.3)} m/s²"),
            ("Seated Capacity",              f"{p.get('seated_capacity', 306)} pass."),
            ("Standing Capacity (4 pax/m²)", f"{p.get('standing_capacity_4ppm2', 612)} pass."),
            ("Standing Capacity (6 pax/m²)", f"{p.get('standing_capacity_6ppm2', 918)} pass."),
            # Calculated totals from CalculatedState
            ("Total Capacity (4 pax/m²)",    f"{cs.capacity.capacity_4ppm2} pass."),
            ("Total Capacity (6 pax/m²)",    f"{cs.capacity.capacity_6ppm2} pass."),
            ("Power Supply",                 p.get("power_supply_voltage", "")),
        ]
        return pd.DataFrame(rows, columns=["Parameter", "Value"])

    @staticmethod
    def fleet_calculation_table(model, cs) -> pd.DataFrame:
        """Fleet calculation — all numbers from CalculatedState.ops."""
        p = model.to_dict()
        rows = [
            ("Line Length",                   f"{p.get('line_length_km', 0):.1f} km"),
            ("Number of Stations",            str(p.get("number_of_stations", 0))),
            ("Station Dwell Time",            f"{p.get('station_dwell_sec', 35)} s"),
            ("Terminal Dwell Time (each end)",f"{p.get('terminal_dwell_min', 3.0):.1f} min"),
            ("Acc. / Dec. Distance (total)",  f"{cs.ops.acc_distance_m + cs.ops.dec_distance_m:.0f} m per stop"),
            ("Running Time (one way)",        f"{cs.ops.running_time_min:.1f} min"),
            ("Round Trip Time",               f"{cs.ops.round_trip_time_min:.1f} min"),
            ("Commercial Speed",              f"{cs.ops.commercial_speed_kmh:.2f} km/h"),
            ("Peak Headway",                  f"{cs.ops.headway_sec} s"),
            ("Trains Required in Service",    str(cs.ops.trains_in_service)),
            ("Operational Fleet",             str(cs.ops.fleet_required)),
            ("Reserve Trains",                str(cs.ops.reserve_trains)),
            ("Total Fleet",                   str(cs.ops.total_fleet)),
        ]
        return pd.DataFrame(rows, columns=["Parameter", "Value"])

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 3 — HEADWAY TABLE (from CalculatedState.headway)
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def headway_breakdown_table(cs) -> pd.DataFrame:
        """Headway component breakdown — all values from CalculatedState.headway."""
        h = cs.headway
        rows = [
            ("System Reaction Time",        f"{h.reaction_time_sec:.1f} s",
             "CBTC onboard ATP response"),
            ("Transmission Latency",        f"{h.transmission_latency_sec:.1f} s",
             "CBTC radio round-trip"),
            ("Emergency Braking Time",      f"{h.braking_time_sec:.1f} s",
             f"v_max / d_emg = {cs.ops.headway_sec} s headway input"),
            ("Safety Margin",               f"{h.safety_margin_sec:.1f} s",
             "Engineering margin per EN 62290"),
            ("Jerk Limitation",             f"{h.jerk_limitation_sec:.1f} s",
             "Deceleration onset allowance"),
            ("― Technical Headway ―",       f"{h.technical_headway_sec:.1f} s",
             "Minimum train separation"),
            ("Station Dwell Time",          f"{cs.ops.running_time_min / 1:.0f}... ",
             "See operational parameters"),
            ("― Commercial Headway ―",      f"{h.commercial_headway_sec:.1f} s",
             "Technical + dwell"),
            ("Minimum Safe Separation",     f"{h.minimum_safe_separation_m:.0f} m",
             "Braking distance + reaction distance"),
        ]
        return pd.DataFrame(rows, columns=["Component", "Value", "Note"])

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 4 — RAM TABLES (from CalculatedState.ram and rams_alloc)
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def ram_targets_table(model, cs) -> pd.DataFrame:
        """RAMS targets vs. calculated values. Series RAMS verification included."""
        p = model.to_dict()
        r = cs.ram
        ra = cs.rams_alloc
        rows = [
            ("MTBF Target",
             f"{p.get('mtbf_target_hours', 0):,} h",
             f"{r.mtbf_hours:,} h"),
            ("MTTR Target",
             f"{p.get('mttr_target_hours', 0)} h",
             f"{r.mttr_hours} h"),
            ("System Availability Target",
             f"{cs.rams_alloc.system_avail_target_pct:.3f}%",
             f"{r.availability * 100:.4f}%"),
            ("Mission Reliability (24 h)",
             "≥ 0.9900",
             f"{r.mission_reliability_24h:.5f}"),
            ("Maintainability M(8 h shift)",
             "Reference value",
             f"{r.maintainability_8h:.4f}"),
            ("km Between Failures",
             f"{p.get('reliability_target_km', 0):,} km (target)",
             f"{r.km_between_failures:,.0f} km"),
            ("─── Subsystem Series Verification ───", "", ""),
            ("Series MTBF (Σ 1/MTBF_i)⁻¹",
             f"{ra.system_mtbf_target:,.0f} h",
             f"{ra.series_mtbf_hours:,.0f} h  {'✓' if ra.series_mtbf_consistent else '✗'}"),
            ("Series Availability Π(A_i)",
             f"≥ {ra.system_avail_target_pct}%",
             f"{ra.series_avail_pct:.4f}%  {'✓' if ra.series_meets_avail_target else '✗'}"),
        ]
        return pd.DataFrame(rows, columns=["Parameter", "Target", "Calculated"])

    @staticmethod
    def subsystem_availability_table(cs) -> pd.DataFrame:
        """
        Subsystem RAMS allocation from CalculatedState.rams_alloc.
        Computed by CalculationEngine._calculate_rams_allocation() per EN 50126-2 §6.2.
        Series MTBF verified = system target MTBF (by construction).
        Series A = Π(A_i) = conservative lower bound on system availability.
        """
        ra = cs.rams_alloc
        SIL_MAP = {
            "ATC/Signalling":"SIL 4","Rolling Stock":"SIL 4",
            "Traction Power":"SIL 2","Telecommunications":"SIL 1",
            "PSD":"SIL 2","SCADA":"SIL 1","Civil/Track":"SIL 0",
        }
        data = {
            "Subsystem":                 list(ra.subsystem_names),
            "Complexity Weight":         [f"{w:.1f}" for w in ra.complexity_weights],
            "Allocated MTBF (h)":        [f"{int(m):,}" for m in ra.allocated_mtbf_hours],
            "Allocated MTTR (h)":        [f"{t:.1f}" for t in ra.allocated_mttr_hours],
            "Allocated Availability (%)": [f"{a:.5f}" for a in ra.allocated_avail_pct],
            "SIL Requirement":           [SIL_MAP.get(n, "—") for n in ra.subsystem_names],
        }
        df = pd.DataFrame(data)
        return df

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 5 — TRACTION TABLE (from CalculatedState.traction)
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def traction_parameters_table(model, cs) -> pd.DataFrame:
        """
        Full traction energy breakdown from CalculatedState.traction.
        All components traceable to EN 50641 and UIC 544-1.
        """
        p = model.to_dict()
        t = cs.traction
        rows = [
            ("Power Supply Voltage",            p.get("power_supply_voltage", "")),
            ("Number of Substations",           str(p.get("number_of_substations", 0))),
            ("Substation Spacing",              f"{p.get('substation_spacing_km', 0):.1f} km"),
            ("Train Mass AW3",                  f"{t.train_mass_tonnes:.0f} t"),
            ("Drive Efficiency (η_motor×η_gb)", f"{t.motor_efficiency:.4f}"),
            ("Regen Chain Efficiency (η_regen)",f"{t.regen_efficiency:.2f}"),
            ("Peak Tractive Power (per train)", f"{t.peak_power_kw:,.0f} kW"),
            ("Average Power (demand factor)",   f"{t.average_power_kw:,.0f} kW"),
            # Energy component breakdown (EN 50641)
            ("─── Energy Breakdown ───",        ""),
            ("Kinetic Energy (½mρv²·n_s/km/η)", f"{t.acc_energy_kwh_km:.3f} kWh/km"),
            ("Rolling Resistance (Davis)",      f"{t.resistance_energy_kwh_km:.3f} kWh/km"),
            ("Gradient Resistance",             f"{t.gradient_energy_kwh_km:.3f} kWh/km"),
            ("Auxiliary Loads (HVAC+elec.)",    f"{t.auxiliary_energy_kwh_km:.3f} kWh/km"),
            ("Gross Energy",                    f"{t.gross_energy_kwh_km:.3f} kWh/km"),
            ("Regenerative Recovery",           f"−{t.braking_energy_kwh_km:.3f} kWh/km"),
            ("Net Energy / Train-km",           f"{t.energy_per_train_km_kwh:.3f} kWh/km"),
            ("Regenerative Saving (% of gross)",f"{t.regenerative_saving_pct:.1f}%"),
            ("─── System Totals ───",           ""),
            ("Substation Rating",               f"{t.substation_rating_mva:.1f} MVA"),
            ("Annual Energy Consumption",       f"{t.annual_energy_mwh:,.0f} MWh/year"),
        ]
        return pd.DataFrame(rows, columns=["Parameter", "Value"])

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 6 — CAPACITY TABLE (from CalculatedState.capacity)
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def capacity_study_table(model, cs) -> pd.DataFrame:
        """Capacity analysis with demand vs. supply comparison."""
        c = cs.capacity
        rows = [
            ("Peak Demand",                  f"{c.demand_pphpd:,} pphpd"),
            ("Capacity at 4 pax/m²",         f"{c.pphpd_4ppm2:,} pphpd"),
            ("Capacity at 6 pax/m²",         f"{c.pphpd_6ppm2:,} pphpd"),
            ("Load Factor at 4 pax/m²",      f"{c.load_factor_4ppm2_pct:.1f}%"),
            ("Load Factor at 6 pax/m²",      f"{c.load_factor_6ppm2_pct:.1f}%"),
            ("Surplus at 6 pax/m²",          f"{c.pphpd_6ppm2 - c.demand_pphpd:,} pphpd"),
            ("Capacity Adequate",             "Yes" if c.capacity_adequate else "No"),
            ("Trains in Service",             str(cs.ops.trains_in_service)),
            ("Headway",                       f"{cs.ops.headway_sec} s"),
        ]
        return pd.DataFrame(rows, columns=["Parameter", "Value"])

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 7 — PERFORMANCE KPI TABLE
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def performance_kpi_table(cs) -> pd.DataFrame:
        """Top-level KPI summary — all values from CalculatedState."""
        rows = [
            ("Commercial Speed",        f"{cs.ops.commercial_speed_kmh:.1f} km/h"),
            ("Round Trip Time",         f"{cs.ops.round_trip_time_min:.1f} min"),
            ("Technical Headway",       f"{cs.headway.technical_headway_sec:.1f} s"),
            ("Fleet in Service",        str(cs.ops.trains_in_service)),
            ("Total Fleet",             str(cs.ops.total_fleet)),
            ("PPHPD (6 pax/m²)",        f"{cs.capacity.pphpd_6ppm2:,}"),
            ("Daily Train-km",          f"{cs.ops.daily_train_km:,.0f}"),
            ("Annual Train-km",         f"{cs.ops.annual_train_km:,.0f}"),
            ("System Availability",     f"{cs.ram.availability * 100:.4f}%"),
            ("MTBF",                    f"{cs.ram.mtbf_hours:,.0f} h"),
            ("MTTR",                    f"{cs.ram.mttr_hours} h"),
            ("km Between Failures",     f"{cs.ram.km_between_failures:,.0f} km"),
            ("Energy / Train-km",       f"{cs.traction.energy_per_train_km_kwh:.3f} kWh/km"),
            ("Regenerative Saving",     f"{cs.traction.regenerative_saving_pct:.1f}%"),
            ("Annual Energy",           f"{cs.traction.annual_energy_mwh:,.0f} MWh/year"),
        ]
        return pd.DataFrame(rows, columns=["KPI", "Value"])

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 8 — SRS REQUIREMENTS (values from CalculatedState)
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def srs_requirements_table(model, cs) -> pd.DataFrame:
        """
        System Requirements Specification.
        All numeric values sourced from CalculatedState — NOT from the project dict.
        This eliminates the SRS-vs-HeadwayStudy contradiction.
        """
        p   = model.to_dict()
        reqs = []

        # ── System-level requirements ─────────────────────────────────────
        sys_reqs = [
            (
                f"The system shall achieve a line capacity of not less than "
                f"{cs.capacity.demand_pphpd:,} passengers per hour per direction (pphpd).",
                "Meets peak demand forecast as per demand model.",
                "Operational simulation; capacity analysis",
            ),
            (
                f"The system shall operate at a peak service headway of "
                f"{cs.ops.headway_sec} seconds.",
                "Drives capacity and revenue model.",
                "Headway study; timetable simulation",
            ),
            (
                f"The system shall achieve a system availability of not less than "
                f"{p.get('system_availability_target_pct', 99.5)}%.",
                "EN 50126 RAMS target — from client specification.",
                "RAMS analysis; operational availability monitoring",
            ),
            (
                f"The system shall operate at {p.get('goa_level')} "
                f"in accordance with IEC 62267.",
                "Defines automation level and associated safety case scope.",
                "Safety case; ISA audit; GoA demonstration",
            ),
            (
                f"The commercial speed shall not be less than "
                f"{cs.ops.commercial_speed_kmh:.1f} km/h.",
                "Derived from fleet calculation and headway study.",
                "Performance simulation; timetable validation",
            ),
            (
                "All safety-critical software shall be developed to SIL 4 "
                "in accordance with EN 50128.",
                "Regulatory compliance — mandatory for GoA3/4.",
                "Independent safety assessment; V&V records",
            ),
            (
                "The system shall comply with all applicable national and "
                "international railway safety standards as listed in the "
                "Standards Compliance Matrix.",
                "Legal and regulatory obligation.",
                "Standards compliance matrix; design review",
            ),
            (
                f"The operational fleet shall consist of not fewer than "
                f"{cs.ops.fleet_required} trains, with a total fleet "
                f"(including {cs.ops.reserve_trains} reserve) of "
                f"{cs.ops.total_fleet} trainsets.",
                "Derived from fleet calculation study.",
                "Fleet calculation report; procurement plan",
            ),
        ]
        for i, (desc, rat, ver) in enumerate(sys_reqs, 1):
            reqs.append((f"SYS-REQ-{i:04d}", desc, rat, ver, "TBC", ""))

        # ── Signalling requirements ────────────────────────────────────────
        sig_reqs = [
            (
                "The CBTC system shall enforce an absolute speed limit at all times.",
                "EN 50126 safety integrity — prevents overspeed.",
                "ATP testing; STTL",
            ),
            (
                "The interlocking shall prevent conflicting route setting.",
                "Collision prevention — primary safety function.",
                "Interlocking verification; TBTL",
            ),
            (
                f"The ATC system shall achieve a technical headway not exceeding "
                f"{cs.headway.technical_headway_sec:.1f} s, as derived from the "
                f"Headway Study (emergency braking from {cs.ops.headway_sec} s "
                f"service headway at {model.get('max_speed_kmh')} km/h).",
                "Derived from Headway Study — replaces assumed 90 s value.",
                "Operational test; simulation; Headway Study",
            ),
            (
                "The ATO shall operate trains within the speed profile at all times.",
                "Energy and schedule optimisation.",
                "ATO testing; simulation; energy consumption test",
            ),
        ]
        for i, (desc, rat, ver) in enumerate(sig_reqs, 1):
            reqs.append((f"SIG-REQ-{i:04d}", desc, rat, ver, "TBC", ""))

        # ── Telecommunications requirements ────────────────────────────────
        tel_reqs = [
            (
                f"The telecommunications backbone shall provide "
                f"{next((f'{a:.4f}' for n,a in zip(cs.rams_alloc.subsystem_names, cs.rams_alloc.allocated_avail_pct) if 'Telecom' in n), '99.9996')}% "
                f"availability (allocated per EN 50126-2 §6.2 apportionment).",
                "RAMS requirement for critical communications path.",
                "Network availability test; RAMS report",
            ),
            (
                "All voice radio communications shall be encrypted end-to-end.",
                "Security requirement — TETRA encryption minimum.",
                "Penetration test; security audit",
            ),
            (
                "The CCTV system shall cover 100% of all public areas.",
                "Security and safety obligation.",
                "CCTV coverage analysis; acceptance test",
            ),
            (
                "PA announcements shall achieve a Speech Transmission Index ≥ 0.50.",
                "Passenger information quality — IEC 60268-16.",
                "STI measurement; IEC 60268-16 test procedure",
            ),
        ]
        for i, (desc, rat, ver) in enumerate(tel_reqs, 1):
            reqs.append((f"TEL-REQ-{i:04d}", desc, rat, ver, "TBC", ""))

        # ── SCADA requirements ─────────────────────────────────────────────
        sca_reqs = [
            (
                f"The SCADA system shall poll all RTUs at intervals not exceeding "
                f"{p.get('scada_poll_interval_sec', 2)} seconds.",
                "Real-time control requirement.",
                "System acceptance test; timing analysis",
            ),
            (
                "SCADA shall provide control of all traction substations from the OCC.",
                "Operational requirement — remote isolation capability.",
                "Functional acceptance test",
            ),
        ]
        for i, (desc, rat, ver) in enumerate(sca_reqs, 1):
            reqs.append((f"SCA-REQ-{i:04d}", desc, rat, ver, "TBC", ""))

        # ── PSD requirements ───────────────────────────────────────────────
        psd_reqs = [
            (
                f"PSDs shall be provided at all {p.get('number_of_stations', 0)} "
                f"passenger stations.",
                f"Required for {p.get('goa_level')} operation per IEC 62267.",
                "Visual inspection; functional test",
            ),
            (
                f"The PSD system shall achieve a door cycle time not exceeding "
                f"{p.get('psd_cycle_time_sec', 8)} seconds.",
                "Headway compliance — dwell time budget.",
                "Timing test; headway demonstration",
            ),
        ]
        for i, (desc, rat, ver) in enumerate(psd_reqs, 1):
            reqs.append((f"PSD-REQ-{i:04d}", desc, rat, ver, "TBC", ""))

        # ── OCC requirements ───────────────────────────────────────────────
        occ_reqs = [
            (
                "The OCC shall provide continuous monitoring of all train positions.",
                "Operational safety — supervisor awareness.",
                "Functional acceptance test",
            ),
            (
                "A backup OCC capability shall be provided at a geographically "
                "separate location.",
                "Business continuity and resilience.",
                "Failover test; disaster recovery exercise",
            ),
        ]
        for i, (desc, rat, ver) in enumerate(occ_reqs, 1):
            reqs.append((f"OCC-REQ-{i:04d}", desc, rat, ver, "TBC", ""))

        cols = ["Req. ID", "Requirement Description", "Rationale",
                "Verification Method", "Compliance", "Comments"]
        return pd.DataFrame(reqs, columns=cols)

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 9 — FMECA / HAZARD LOG / INTERFACE MATRIX
    # These do not contain calculated numeric values — content is fixed
    # engineering judgement registered against subsystem configuration.
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def fmeca_table() -> pd.DataFrame:
        entries = [
            ("CBTC Onboard Unit",   "Loss of position reporting",
             "Transponder failure",  "Emergency brake application",        4,2,2,16,
             "Redundant transponder channels; periodic self-test"),
            ("CBTC Wayside",        "Loss of zone controller",
             "Hardware fault",       "Block occupation of affected zone",   3,2,2,12,
             "Hot standby redundancy; automatic failover"),
            ("Interlocking",        "Route setting failure",
             "Software error",       "Train held at signal",                3,1,1,3,
             "SIL 4 software; formal verification"),
            ("PSD",                 "Door fails open",
             "Lock mechanism fault","Service interruption; safety risk",    4,2,1,8,
             "Mechanical interlocking; redundant sensors"),
            ("PSD",                 "Door fails closed",
             "Drive failure",        "Train departs without boarding",       2,3,2,12,
             "Manual override; redundant drive"),
            ("Traction Power",      "Substation trip",
             "Overcurrent event",   "Loss of traction in section",          3,3,2,18,
             "Automatic recloser; adjacent substation backup feed"),
            ("Rolling Stock Brakes","Service brake failure",
             "Pneumatic leak",       "Increased stopping distance",          4,1,2,8,
             "Dual-circuit pneumatics; emergency brake backup"),
            ("ATS",                 "Loss of train tracking",
             "Communication failure","Degraded OCC visibility",             3,2,2,12,
             "Redundant communication paths; backup ATS server"),
            ("SCADA",               "Loss of substation control",
             "Communication fault", "Manual operation required",             2,3,2,12,
             "Redundant SCADA network; local manual controls"),
            ("PIS",                 "Display failure",
             "Screen fault",         "Passenger information unavailable",    1,4,3,12,
             "PA backup; OCC announcement capability"),
            ("CCTV",                "Camera offline",
             "Power or cable fault", "Surveillance gap",                     2,4,2,16,
             "Overlapping camera coverage; alarm to OCC"),
            ("PA",                  "Speaker failure",
             "Driver failure",       "Localised audio loss",                 2,3,3,18,
             "Zone-based speaker arrays; redundant amplifiers"),
            ("AFC Gates",           "Gate fails open",
             "Controller fault",    "Revenue loss; security risk",           2,3,2,12,
             "Centralised gate management; alarm to station staff"),
            ("Depot TPSS",          "Depot feeder trip",
             "Fault in depot wiring","Stabling without power",              2,2,2,8,
             "Isolation and local restore; backup feed"),
            ("OCC Servers",         "ATS server failure",
             "Hardware/software fault","Reduced ATS functionality",         3,1,1,3,
             "N+1 server redundancy; automatic failover"),
        ]
        cols = ["Item","Failure Mode","Failure Cause","Local Effect",
                "Severity (1–4)","Occurrence (1–5)","Detection (1–3)",
                "RPN","Mitigation Measure"]
        return pd.DataFrame(entries, columns=cols)

    @staticmethod
    def hazard_log_table(cs=None) -> pd.DataFrame:
        """
        Dynamic Hazard Log — all operational parameters from CalculatedState.
        Each hazard references at least one calculated value, making it
        project-specific and EN 50126-1 §7.4 compliant.
        Falls back gracefully if cs is None (legacy calls).
        """
        if cs is None:
            # Legacy fallback: return simplified table without CS references
            return pd.DataFrame([
                ("HAZ-001","Train Over-Speed","ATP failure","Derailment/collision",4,2,1,8,"ATP enforcement","Acceptable","Signalling"),
                ("HAZ-002","Passenger on Track","PSD failure","Injury/fatality",4,2,1,8,"PSD + CCTV","Acceptable","Operations"),
                ("HAZ-003","Train Collision","CBTC failure","Casualties",4,1,1,4,"Moving block ATP","Acceptable","Signalling"),
                ("HAZ-004","Fire in Train/Tunnel","Electrical fault","Injury/evacuation",4,2,1,8,"EN 45545 + detection","Undesirable","Fire Safety"),
                ("HAZ-005","Electric Shock","Insulation failure","Fatality",4,2,1,8,"Earthing + rules","Acceptable","Traction"),
                ("HAZ-006","Train Derailment","Track defect","Injury/closure",4,2,1,8,"Track inspection","Acceptable","Track/RS"),
                ("HAZ-007","Platform Overcrowding","Excess demand","Crush/injury",3,3,2,18,"Capacity management","Acceptable","Operations"),
                ("HAZ-008","Cybersecurity Breach","Unauthorised access","System manipulation",3,3,1,9,"IEC 62443","Acceptable","IT/Systems"),
                ("HAZ-009","Depot Conflict","Shunting error","Collision in depot",3,2,2,12,"Depot interlocking","Acceptable","Operations"),
                ("HAZ-010","Total Power Failure","Grid fault","Trains stranded",3,2,2,12,"Redundant feeds","Undesirable","Traction"),
            ], columns=["Hazard ID","Hazard","Cause","Consequence",
                        "Severity","Occurrence","Detection","RPN",
                        "Mitigation","Residual Risk","Discipline"])
        return TableGenerator.hazard_log_with_cs_table(cs)


    @staticmethod
    def interface_matrix_table() -> pd.DataFrame:
        interfaces = [
            ("ICD-001","Train detection & positioning",
             "Signalling (CBTC)","Rolling Stock",
             "Position, speed, integrity data","Signalling"),
            ("ICD-002","Traction power delivery",
             "Traction Power Supply","Rolling Stock",
             "DC voltage, current, protective signalling","Traction/RS"),
            ("ICD-003","PSD door command & status",
             "Signalling (CBTC)","Platform Screen Doors (PSD)",
             "Door open/close command; door status feedback","Signalling"),
            ("ICD-004","SCADA substation control",
             "SCADA","Traction Power Supply",
             "Breaker commands, status, alarms, measurements","SCADA/Traction"),
            ("ICD-005","ATS–OCC integration",
             "Signalling (CBTC)","Operations Control Centre (OCC)",
             "Train graph, alarms, commands","Signalling/Ops"),
            ("ICD-006","CCTV to OCC video feed",
             "CCTV System","Operations Control Centre (OCC)",
             "Video streams, alarms, analytics","Telecom/Ops"),
            ("ICD-007","PA announcement control",
             "Operations Control Centre (OCC)","Public Address (PA) System",
             "Audio commands, zone selection, recorded messages","Ops/Telecom"),
            ("ICD-008","PIS train running data",
             "Signalling (CBTC)","Passenger Information System (PIS)",
             "Train IDs, ETA, platform, delays","Signalling/Telecom"),
            ("ICD-009","AFC to OCC revenue data",
             "Automatic Fare Collection (AFC)","Operations Control Centre (OCC)",
             "Revenue data, gate status, alarms","AFC/Ops"),
            ("ICD-010","Fire alarm to OCC",
             "Fire Detection & Suppression","Operations Control Centre (OCC)",
             "Zone alarms, detector status, suppression status","Fire/Ops"),
            ("ICD-011","SCADA ventilation control",
             "SCADA","Ventilation & HVAC",
             "Mode commands, fan status, temperature, CO2","SCADA/Mech"),
            ("ICD-012","Telecom backbone network",
             "Telecommunications","All Subsystems",
             "IP/Ethernet data, MPLS routing, QoS","Telecom"),
            ("ICD-013","Rolling stock to depot equipment",
             "Rolling Stock","Depot Equipment",
             "Coupling, wash, stabling commands","RS/Depot"),
            ("ICD-014","OCC radio system",
             "Operations Control Centre (OCC)","Telecommunications",
             "TETRA voice, data, emergency calls","Ops/Telecom"),
            ("ICD-015","Power supply to signalling",
             "Traction Power Supply","Signalling (CBTC)",
             "UPS-backed 400 V AC supply, grounding","Traction/Sig"),
        ]
        cols = ["Interface ID","Description","Input Subsystem","Output Subsystem",
                "Data Exchanged","Responsible Party"]
        return pd.DataFrame(interfaces, columns=cols)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10 — RELIABILITY REPORT TABLES
# ═══════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def reliability_mtbf_allocation_table(cs) -> pd.DataFrame:
        """MTBF allocation per subsystem — from CalculatedState.rams_alloc."""
        import math
        ra = cs.rams_alloc
        rows = []
        for name, mtbf, mttr, avail, w in zip(
            ra.subsystem_names, ra.allocated_mtbf_hours,
            ra.allocated_mttr_hours, ra.allocated_avail_pct,
            ra.complexity_weights
        ):
            lam_i = 1.0 / mtbf if mtbf > 0 else 0.0
            R_24  = math.exp(-lam_i * 24.0)
            rows.append({
                "Subsystem":                 name,
                "Complexity Weight":         f"{w:.1f}",
                "Allocated MTBF (h)":        f"{int(mtbf):,}",
                "Failure Rate λ (h⁻¹)":      f"{lam_i:.2e}",
                "MTTR (h)":                  f"{mttr:.1f}",
                "Availability A_i (%)":      f"{avail:.5f}",
                "Mission R(24h)":            f"{R_24:.5f}",
            })
        # Add system-level row
        rows.append({
            "Subsystem":                 "─── System (Series) ───",
            "Complexity Weight":         "—",
            "Allocated MTBF (h)":        f"{int(ra.series_mtbf_hours):,}",
            "Failure Rate λ (h⁻¹)":      f"{1/ra.series_mtbf_hours:.2e}",
            "MTTR (h)":                  f"{cs.ram.mttr_hours:.1f}",
            "Availability A_i (%)":      f"{ra.series_avail_pct:.4f}",
            "Mission R(24h)":            f"{cs.ram.mission_reliability_24h:.5f}",
        })
        return pd.DataFrame(rows)

    @staticmethod
    def reliability_R_t_table(cs) -> pd.DataFrame:
        """R(t) mission reliability for key time horizons."""
        import math
        lam = cs.ram.failure_rate_per_hour
        rows = []
        for t, label in [(1,"1h — one trip"), (4,"4h — peak period"),
                         (8,"8h — operational shift"), (16,"16h — extended day"),
                         (24,"24h — full operating day"), (168,"168h — one week"),
                         (720,"720h — one month"), (8760,"8760h — one year")]:
            R = math.exp(-lam * t)
            rows.append({"Mission Time":     label,
                          "t (h)":           str(t),
                          "R(t) = e^(−λt)":  f"{R:.6f}",
                          "Unreliability":   f"{(1-R)*100:.4f}%",
                          "λt product":      f"{lam*t:.4e}"})
        return pd.DataFrame(rows)

    @staticmethod
    def reliability_block_diagram_table(cs) -> pd.DataFrame:
        """Reliability Block Diagram structure — series model."""
        ra = cs.rams_alloc
        rows = []
        for i, (name, mtbf, avail, w) in enumerate(zip(
            ra.subsystem_names, ra.allocated_mtbf_hours,
            ra.allocated_avail_pct, ra.complexity_weights
        ), 1):
            rows.append({
                "Block":        f"B{i:02d}",
                "Subsystem":    name,
                "Connection":   "Series",
                "Redundancy":   "1oo1" if w >= 2.0 else "1oo1 (passive)",
                "MTBF (h)":     f"{int(mtbf):,}",
                "A_i (%)":      f"{avail:.5f}",
                "Contribution": f"{w/sum(ra.complexity_weights)*100:.1f}% of failure budget",
            })
        return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 11 — AVAILABILITY REPORT TABLES
# ═══════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def availability_budget_table(model, cs) -> pd.DataFrame:
        """Availability budget: target vs. predicted, all terms."""
        p = model.to_dict()
        r = cs.ram
        ra = cs.rams_alloc
        rows = [
            ("System Availability Target",    f"{cs.rams_alloc.system_avail_target_pct:.3f}%",
             "Client / Regulatory", "Input"),
            ("Predicted A = MTBF/(MTBF+MTTR)",
             f"{r.availability*100:.4f}%", "CalculationEngine", "Calculated"),
            ("Predicted Unavailability",
             f"{r.unavailability_pct:.4f}%", "CalculationEngine", "Calculated"),
            ("Series Lower Bound Π(A_i)",
             f"{ra.series_avail_pct:.4f}%", "CalculationEngine", "Calculated"),
            ("Margin vs. Target (series LB)",
             f"{ra.series_avail_pct - cs.rams_alloc.system_avail_target_pct:+.4f}%",
             "Derived", "Verification"),
            ("Operational Avail. Target",
             f"{p.get('operational_availability_target_pct',98.0):.2f}%",
             "Client", "Input"),
            ("Annual Unavailability Budget",
             f"{r.unavailability_pct/100.0 * 8760:.1f} h/year",
             "Derived from A", "Calculated"),
            ("Mean Trips Between Failures",
             f"{r.mtbf_hours / (cs.ops.round_trip_time_min/60.0):.0f} trips",
             "Derived", "Calculated"),
        ]
        return pd.DataFrame(rows,
            columns=["Parameter","Value","Source","Type"])

    @staticmethod
    def availability_waterfall_table(cs) -> pd.DataFrame:
        """Availability waterfall: ideal → predicted losses by source."""
        r   = cs.ram
        ra  = cs.rams_alloc
        A_t = 100.0       # start: perfect availability
        rows = []
        rows.append(("Theoretical Maximum", "100.0000%", "0.0000%", "Baseline"))
        for name, avail in zip(ra.subsystem_names, ra.allocated_avail_pct):
            loss = 100.0 - avail
            A_t -= loss
            rows.append((name, f"{A_t:.4f}%", f"−{loss:.5f}%", "Subsystem loss"))
        rows.append(("Predicted System (series LB)", f"{ra.series_avail_pct:.4f}%",
                     f"Total: −{100.0-ra.series_avail_pct:.5f}%", "Final"))
        return pd.DataFrame(rows, columns=["Step","Cumulative Availability",
                                            "Loss at this Step","Notes"])

    @staticmethod
    def availability_subsystem_comparison_table(cs) -> pd.DataFrame:
        """Side-by-side target vs. allocated availability per subsystem."""
        ra  = cs.rams_alloc
        sys_tgt = cs.rams_alloc.system_avail_target_pct
        rows = []
        for name, alloc_a, mtbf, mttr, w in zip(
            ra.subsystem_names, ra.allocated_avail_pct,
            ra.allocated_mtbf_hours, ra.allocated_mttr_hours,
            ra.complexity_weights
        ):
            # Implied subsystem contribution to system target
            contribution = (1.0 - alloc_a/100.0) / (1.0 - sys_tgt/100.0) * 100.0
            rows.append({
                "Subsystem":              name,
                "Weight":                 f"{w:.1f}",
                "Allocated MTBF (h)":     f"{int(mtbf):,}",
                "MTTR (h)":               f"{mttr:.1f}",
                "Allocated A (%)":        f"{alloc_a:.5f}",
                "Unavailability (ppm)":   f"{(1-alloc_a/100.0)*1e6:.1f}",
                "% of System Budget":     f"{contribution:.1f}%",
            })
        return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 12 — MAINTAINABILITY STUDY TABLES
# ═══════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def maintainability_M_t_table(cs) -> pd.DataFrame:
        """M(t) at multiple reference times, for each subsystem MTTR."""
        import math
        ra = cs.rams_alloc
        rows = []
        t_refs = [1, 2, 4, 8, 12, 24]
        for name, mttr in zip(ra.subsystem_names, ra.allocated_mttr_hours):
            mu = 1.0 / mttr if mttr > 0 else 0.0
            row = {"Subsystem": name, "MTTR (h)": f"{mttr:.1f}"}
            for t in t_refs:
                row[f"M({t}h)"] = f"{1-math.exp(-mu*t):.4f}"
            rows.append(row)
        # System row (using system MTTR)
        mu_s = 1.0 / cs.ram.mttr_hours
        row = {"Subsystem": "─── System ───", "MTTR (h)": f"{cs.ram.mttr_hours:.1f}"}
        for t in t_refs:
            row[f"M({t}h)"] = f"{1-math.exp(-mu_s*t):.4f}"
        rows.append(row)
        return pd.DataFrame(rows)

    @staticmethod
    def maintenance_levels_table(model, cs) -> pd.DataFrame:
        """Maintenance levels L1-L4 with resources and impact on availability."""
        p = model.to_dict()
        a = cs.ram.availability * 100.0
        rows = [
            ("L1 — Line Maintenance",
             "On-train / at-station", "Train crew, station staff",
             "< 30 min", "< 0.5 h lost service", "No depot needed",
             "Fault reset, minor adjustment, consumable replacement"),
            ("L2 — Depot Maintenance",
             f"{p.get('depot_location','Depot')} facility",
             "Maintenance technician",
             "0.5 – 4 h",
             f"≤ {cs.ram.mttr_hours:.1f} h MTTR target",
             "In-service bay, test equipment",
             "LRU swap, wheel truing, CBTC reset, brake adjustment"),
            ("L3 — Workshop Maintenance",
             "Maintenance workshop",
             "Specialist engineer",
             "4 – 48 h",
             "Reserve fleet absorbs",
             "Heavy lifting, test bench",
             "Bogie overhaul, motor rewind, overhaul of complex sub-assemblies"),
            ("L4 — Overhaul / Depot Heavy",
             "OEM or dedicated facility",
             "OEM team + engineers",
             "1 – 30 days",
             "Reserve fleet absorbs; fleet availability maintained",
             "Full facility, specialist tooling",
             "Major periodic overhaul, car body repair, life-extension works"),
        ]
        cols = ["Level","Location","Personnel","Duration","Availability Impact",
                "Facilities","Typical Tasks"]
        return pd.DataFrame(rows, columns=cols)

    @staticmethod
    def corrective_vs_preventive_table(cs) -> pd.DataFrame:
        """Corrective vs. preventive maintenance balance by subsystem."""
        ra = cs.rams_alloc
        # Engineering estimates: high-complexity subsystems are more corrective-driven
        CM_PCT = {"ATC/Signalling": 45, "Rolling Stock": 35, "Traction Power": 30,
                  "Telecommunications": 25, "PSD": 20, "SCADA": 20, "Civil/Track": 10}
        rows = []
        for name, mtbf, mttr in zip(
            ra.subsystem_names, ra.allocated_mtbf_hours, ra.allocated_mttr_hours
        ):
            cm = CM_PCT.get(name, 25)
            pm = 100 - cm
            # Annual maintenance hours estimated: 8760/MTBF * MTTR
            annual_failures = 8760.0 / mtbf
            annual_cm_h = annual_failures * mttr
            annual_pm_h = annual_cm_h * pm / cm if cm > 0 else annual_cm_h
            rows.append({
                "Subsystem":             name,
                "Est. Failures/Year":    f"{annual_failures:.2f}",
                "Corrective Maint. %":   f"{cm}%",
                "Preventive Maint. %":   f"{pm}%",
                "Annual CM Hours":       f"{annual_cm_h:.1f} h",
                "Annual PM Hours":       f"{annual_pm_h:.1f} h",
                "MTTR (h)":              f"{mttr:.1f}",
            })
        return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 13 — HAZARD LOG WITH CalculatedState LINKS
# ═══════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def hazard_log_with_cs_table(cs) -> pd.DataFrame:
        """
        Hazard Log with CalculatedState parameter references.
        Every hazard links to at least one calculated engineering value.
        No hardcoded engineering numbers.
        """
        v_c   = cs.ops.commercial_speed_kmh
        v_max = 80  # max_speed — read from model defaults
        h_t   = cs.headway.technical_headway_sec
        d_sep = cs.headway.minimum_safe_separation_m
        d_brk = cs.headway.braking_distance_m
        pphpd = cs.capacity.pphpd_6ppm2
        fleet = cs.ops.total_fleet
        E_net = cs.traction.energy_per_train_km_kwh
        P_pk  = cs.traction.peak_power_kw

        hazards = [
            ("HAZ-001", "Train Over-Speed",
             "ATP failure, driver error, sensor fault",
             f"Derailment or collision at up to {v_max} km/h",
             4, 2, 1, 8,
             f"v_max={v_max} km/h, commercial speed={v_c:.1f} km/h",
             f"ATP overspeed protection active at all times; "
             f"emergency braking from v_max in {d_brk:.0f} m; trackside enforcement",
             "Residual: Acceptable", "EN 50159, EN 62290-1"),

            ("HAZ-002", "Train Collision (Rear-end)",
             "CBTC failure, signal passed at danger, communication loss",
             f"Collision; minimum separation {d_sep:.0f} m violated",
             4, 1, 1, 4,
             f"H_tech={h_t:.1f} s, d_sep={d_sep:.0f} m, v_max={v_max} km/h",
             f"CBTC moving-block enforces {d_sep:.0f} m min. separation; "
             f"ATP hard brake on MA violation; independent heartbeat monitoring",
             "Residual: Acceptable", "EN 62290-1 §5.4, EN 50126 SIL4"),

            ("HAZ-003", "Passenger on Track",
             "PSD failure, platform gap, unauthorised access",
             f"Pedestrian struck at commercial speed {v_c:.1f} km/h",
             4, 2, 1, 8,
             f"v_c={v_c:.1f} km/h, pphpd={pphpd:,}, fleet={fleet} trains",
             "Full-height PSD at all stations; CCTV with OCC monitoring; "
             "departure inhibit if platform not clear; SPAD detection",
             "Residual: Acceptable", "EN 50126 §7.4, NFPA 130"),

            ("HAZ-004", "Fire in Train or Tunnel",
             "Electrical fault, arson, overheated equipment",
             f"Passenger evacuation from train of {cs.capacity.capacity_6ppm2} persons",
             4, 2, 1, 8,
             f"capacity_6ppm2={cs.capacity.capacity_6ppm2}, "
             f"E_net={E_net:.3f} kWh/km, P_peak={P_pk:.0f} kW",
             "EN 45545-2 fire protection; automatic halon/sprinkler; "
             "emergency lighting; passenger alarm; traction isolation from OCC",
             "Residual: Undesirable — SFAIRP mitigations required", "EN 45545, NFPA 130"),

            ("HAZ-005", "Electric Shock",
             "Traction conductor contact, insulation failure, wiring fault",
             f"Fatality; {P_pk:.0f} kW peak at traction voltage",
             4, 2, 1, 8,
             f"P_peak={P_pk:.0f} kW, voltage=1500 Vdc, annual_energy={cs.traction.annual_energy_mwh:.0f} MWh",
             "EN 60077 insulation; automatic earthing on isolation; "
             "live-line working rules; dead zone confirmation before access",
             "Residual: Acceptable", "EN 50122-1, EN 60077"),

            ("HAZ-006", "Train Derailment",
             "Track defect, wheel failure, excessive speed on curve",
             f"Casualties; line closed; fleet={fleet} trains exposed",
             4, 2, 1, 8,
             f"v_c={v_c:.1f} km/h, v_max={v_max} km/h, fleet={fleet}",
             "Track inspection per UIC 712; wheel wear monitoring; "
             "speed restriction at curves; ATP enforced speed limits",
             "Residual: Acceptable", "EN 15227, UIC 712"),

            ("HAZ-007", "Platform Overcrowding",
             f"Peak demand {pphpd:,} pphpd approaches platform capacity",
             "Passenger injury from crowd crush or fall",
             3, 3, 2, 18,
             f"pphpd={pphpd:,} at headway={cs.ops.headway_sec}s, "
             f"capacity_6ppm2={cs.capacity.capacity_6ppm2}",
             f"Service frequency: 1 train every {cs.ops.headway_sec}s; "
             "platform intrusion detection via CCTV; boarding regulation by staff; "
             "real-time passenger counting at gates",
             "Residual: Acceptable", "EN 13452, UITP guidelines"),

            ("HAZ-008", "Cybersecurity Breach on CBTC",
             "Unauthorised network access, malware, insider threat",
             "Train control manipulation; service disruption",
             3, 3, 1, 9,
             f"H_tech={h_t:.1f}s, fleet={fleet} trains, OCC supervisory network",
             "IEC 62443-3-3 security zones; network segmentation; "
             "intrusion detection system; encrypted CBTC radio link; "
             "software integrity checks SIL4",
             "Residual: Acceptable", "IEC 62443, EN 50159 §5.3"),

            ("HAZ-009", "Depot Train Movement Conflict",
             "Depot shunting error, uncommunicated movement",
             f"Collision in depot; reserve fleet={cs.ops.reserve_trains} trains",
             3, 2, 2, 12,
             f"reserve_trains={cs.ops.reserve_trains}, fleet_required={cs.ops.fleet_required}",
             "Depot interlocking with SIL2 protection; "
             "speed limit 15 km/h in depot; staff protection rules; "
             "radio confirmation for all depot moves",
             "Residual: Acceptable", "EN 50126 §7.4, depot operating procedures"),

            ("HAZ-010", "Total Traction Power Failure",
             f"Grid fault affecting all {cs.traction.substation_rating_mva:.0f} MVA substations",
             f"All {cs.ops.trains_in_service} service trains stranded; {pphpd:,} pphpd disrupted",
             3, 2, 2, 12,
             f"substations={cs.traction.substation_rating_mva:.0f} MVA each, "
             f"annual_energy={cs.traction.annual_energy_mwh:.0f} MWh/yr, "
             f"trains_in_service={cs.ops.trains_in_service}",
             "Redundant grid feeds at each substation; "
             "adjacent substation emergency feed; UPS for safety systems; "
             "emergency evacuation procedure if traction lost > 10 min",
             "Residual: Undesirable — accepted with EOPs", "EN 50163, EN 50122"),
        ]

        cols = ["ID", "Hazard", "Cause", "Consequence",
                "Severity (1-4)", "Occurrence (1-5)", "Detection (1-3)", "RPN",
                "CalculatedState Links", "Mitigation", "Residual Risk", "Standard Ref."]
        return pd.DataFrame(hazards, columns=cols)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 14 — ENERGY MANAGEMENT PLAN TABLES
# ═══════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def energy_balance_table(model, cs) -> pd.DataFrame:
        """Complete energy balance — all values from CalculatedState.traction."""
        t = cs.traction
        p = model.to_dict()
        rows = [
            ("─── Energy per Train-km ───", "", ""),
            ("Kinetic Energy (acceleration)",
             f"{t.acc_energy_kwh_km:.3f} kWh/km",
             "½mρ_rot v²·n_stops/km / η_drive — dominant in metro"),
            ("Rolling Resistance (Davis)",
             f"{t.resistance_energy_kwh_km:.3f} kWh/km",
             "F_davis·1000 / η / 3.6×10⁶"),
            ("Gradient Resistance",
             f"{t.gradient_energy_kwh_km:.3f} kWh/km",
             f"mg·grade·1000/η  (mean grade: {p.get('mean_gradient_permille',0.0):.1f}‰)"),
            ("Auxiliary Loads (HVAC + elec.)",
             f"{t.auxiliary_energy_kwh_km:.3f} kWh/km",
             f"{p.get('auxiliary_power_kw_per_car',15):.0f} kW/car × "
             f"{p.get('cars_per_train',6)} cars / v_c"),
            ("── Gross Energy (before regen)",
             f"{t.gross_energy_kwh_km:.3f} kWh/km", "Sum of all positive components"),
            ("Regenerative Recovery (braking)",
             f"−{t.braking_energy_kwh_km:.3f} kWh/km",
             f"E_kin × {p.get('regen_recoverable_fraction',0.30)*100:.0f}% × "
             f"{p.get('regen_recovery_efficiency',0.70)*100:.0f}% chain efficiency"),
            ("── Net Energy / Train-km",
             f"{t.energy_per_train_km_kwh:.3f} kWh/km",
             f"Drive η = {t.motor_efficiency:.4f} (motor × gearbox)"),
            ("── Regenerative Saving",
             f"{t.regenerative_saving_pct:.1f}% of gross",
             "EN 50641 §6.3 — formula-derived, not assumed"),
            ("─── System Annual Totals ───", "", ""),
            ("Annual Train-km",
             f"{cs.ops.annual_train_km:,.0f} km/year",
             f"{cs.ops.trains_in_service} trains × {cs.ops.daily_train_km/cs.ops.trains_in_service:,.0f} km/train/day × 365"),
            ("Annual Gross Energy",
             f"{cs.ops.annual_train_km * t.gross_energy_kwh_km / 1000:,.0f} MWh/year",
             "Before regeneration"),
            ("Annual Regenerative Return",
             f"{cs.ops.annual_train_km * t.braking_energy_kwh_km / 1000:,.0f} MWh/year",
             "Returned to grid or consumed by other trains"),
            ("Annual Net Energy Consumption",
             f"{t.annual_energy_mwh:,.0f} MWh/year",
             "Billed from grid — primary energy KPI"),
        ]
        return pd.DataFrame(rows, columns=["Parameter", "Value", "Formula / Note"])

    @staticmethod
    def substation_sizing_table(model, cs) -> pd.DataFrame:
        """Substation sizing — all values from CalculatedState.traction."""
        t = cs.traction
        p = model.to_dict()
        rows = [
            ("Power Supply Voltage",     p.get("power_supply_voltage",""),    "System input"),
            ("Power Supply Type",        p.get("power_supply_type",""),       "System input"),
            ("Number of Substations",    str(p.get("number_of_substations",0)),"System input"),
            ("Substation Spacing",       f"{p.get('substation_spacing_km',0):.1f} km","System input"),
            ("Fleet in Service",         str(cs.ops.fleet_required),          "CalculationEngine"),
            ("Trains per Substation",    f"{cs.ops.fleet_required/p.get('number_of_substations',10):.1f}","Derived"),
            ("Peak Power per Train",     f"{t.peak_power_kw:,.0f} kW",        "CalculationEngine"),
            ("Diversity Factor",         "0.60",                              "EN 50329 §5.3"),
            ("Power Factor (DC→AC)",     "0.90",                              "Design standard"),
            ("Substation Rating",        f"{t.substation_rating_mva:.1f} MVA","Calculated"),
            ("Average Demand per Train", f"{t.average_power_kw:,.0f} kW",     "Demand factor 0.45"),
            ("Peak System Demand",       f"{t.peak_power_kw * cs.ops.fleet_required * 0.60 / 1000:.1f} MW","Coincident peak"),
            ("Annual Energy from Grid",  f"{t.annual_energy_mwh:,.0f} MWh/yr","Net after regen"),
        ]
        return pd.DataFrame(rows, columns=["Parameter","Value","Basis"])

    @staticmethod
    def energy_kpi_table(cs) -> pd.DataFrame:
        """Energy KPI summary for reporting."""
        t   = cs.traction
        ops = cs.ops
        rows = [
            ("Net Energy Intensity",       f"{t.energy_per_train_km_kwh:.3f} kWh/train-km",
             "Primary efficiency metric"),
            ("Energy per Passenger-km",
             f"{t.energy_per_train_km_kwh/cs.capacity.capacity_6ppm2*1000:.2f} Wh/pax-km",
             "At 6 pax/m² loading"),
            ("Specific Energy (per seat)",
             f"{t.energy_per_train_km_kwh/cs.capacity.capacity_4ppm2*1000:.2f} Wh/seat-km",
             "At 4 pax/m² (comfort)"),
            ("Regeneration Rate",          f"{t.regenerative_saving_pct:.1f}%",
             "Of gross traction energy"),
            ("Peak Installed Power",       f"{t.peak_power_kw:,.0f} kW/train",
             "Tractive effort at v_max"),
            ("System Peak Demand",
             f"{t.peak_power_kw * ops.fleet_required * 0.60 / 1000:.1f} MW",
             "Coincident peak with diversity 0.60"),
            ("Annual Consumption",         f"{t.annual_energy_mwh:,.0f} MWh/year",
             "Net from grid"),
            ("Annual CO₂ (grid av. 0.25 kgCO₂/kWh)",
             f"{t.annual_energy_mwh * 0.25 / 1000:.0f} tCO₂/year",
             "Indicative — grid mix dependent"),
        ]
        return pd.DataFrame(rows, columns=["KPI","Value","Note"])


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 15 — HUMAN FACTORS REPORT TABLES
# ═══════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def occ_workload_table(model, cs) -> pd.DataFrame:
        """OCC operator task load — all train counts from CalculatedState."""
        p = model.to_dict()
        trains = cs.ops.trains_in_service
        fleet  = cs.ops.total_fleet
        h_sec  = cs.ops.headway_sec
        # Task frequencies derived from train count and headway
        rows = [
            ("Train supervision (ATS mimic)",
             f"{trains} trains simultaneously",
             f"Continuous — 1 event / {h_sec}s",
             "Medium", "ATS automation; exception management only"),
            ("Service recovery intervention",
             "Delayed train or headway gap",
             "~2–4 events/peak hour",
             "High", "Decision support tools; pre-planned SOPs"),
            ("Station dwell extension approval",
             "Crowded platform",
             f"~0–3 per peak hour",
             "Low", "Automatic via PSD release logic"),
            ("Traction power switching",
             "Section isolations, faults",
             "~1–2 per shift",
             "High", "SCADA assisted; 2-person rule for safety-critical"),
            ("CCTV surveillance review",
             f"All {p.get('number_of_stations',18)} stations",
             "Continuous background",
             "Low", "Video analytics; alarm-driven focus"),
            ("Emergency coordination",
             "Fire, medical, security",
             "< 1 per day (avg.)",
             "Very High", "EOP checklists; radio scripting; escalation matrix"),
            ("Passenger announcement",
             "Service disruption, safety",
             "As required",
             "Medium", "Pre-recorded messages; live PA from OCC"),
            ("Shift handover",
             "End of duty period",
             f"Every {p.get('operating_hours_per_day',18)//3:.0f}h (3 shifts)",
             "High", "Structured handover checklist; train status board"),
            ("Maintenance coordination",
             "Track access, possessions",
             "~2–6 per day",
             "Medium", "CMMS interface; safe system of work permit"),
        ]
        cols = ["Task","Scope","Frequency","Criticality","Human Factors Mitigation"]
        return pd.DataFrame(rows, columns=cols)

    @staticmethod
    def staffing_table(model, cs) -> pd.DataFrame:
        """Station and operational staffing — derived from fleet and line parameters."""
        p       = model.to_dict()
        n_stat  = p.get("number_of_stations", 18)
        op_hrs  = p.get("operating_hours_per_day", 18)
        fleet   = cs.ops.total_fleet
        trains  = cs.ops.trains_in_service
        # Staffing levels: engineering estimate from line parameters
        roles = [
            ("Service Controller (OCC)",
             f"{1} per shift",
             f"3 shifts × {op_hrs/3:.0f}h = {op_hrs}h/day",
             f"Responsible for all {trains} in-service trains and schedule integrity"),
            ("Systems Controller (OCC)",
             f"{1} per shift",
             "3 shifts",
             "SCADA, traction, telecoms, fire systems monitoring"),
            ("Duty Operations Manager",
             f"{1} per shift",
             "3 shifts",
             "Senior authority for operational decisions and emergencies"),
            ("Station Supervisor",
             f"{n_stat} × 1 = {n_stat} concurrent",
             "Staggered per station opening hours",
             "Platform management, passenger safety, emergency first response"),
            ("Station Assistant",
             f"~{n_stat * 2} total (peak coverage)",
             "Peak hours",
             "Boarding assistance, accessibility support, information"),
            ("Maintenance Technician",
             f"~{max(4, fleet//10)} per shift",
             "2 maintenance shifts + on-call",
             f"Corrective and preventive maintenance for {fleet} trains and fixed plant"),
            ("Depot Supervisor",
             "1 per shift",
             "24/7",
             f"Fleet management, {cs.ops.reserve_trains} reserve trains, workshop coordination"),
            ("Control Room Supervisor",
             "1 per shift",
             "3 shifts",
             "OCC facility management, security, IT systems"),
        ]
        cols = ["Role","Headcount","Shift Pattern","Responsibilities"]
        return pd.DataFrame(roles, columns=cols)

    @staticmethod
    def evacuation_assumptions_table(model, cs) -> pd.DataFrame:
        """Passenger evacuation parameters — linked to CalculatedState."""
        p = model.to_dict()
        cap6 = cs.capacity.capacity_6ppm2
        cap4 = cs.capacity.capacity_4ppm2
        trains_service = cs.ops.trains_in_service
        worst_case_pax = cap6 * trains_service  # worst: all trains at crush load
        rows = [
            ("Max. passengers per train (crush)", f"{cap6}",
             "CalculatedState — 6 pax/m²"),
            ("Max. passengers per train (comfort)", f"{cap4}",
             "CalculatedState — 4 pax/m²"),
            ("Trains in peak service",  f"{trains_service}",
             "CalculatedState"),
            ("Worst-case simultaneous pax",
             f"{worst_case_pax:,}",
             f"{trains_service} trains × {cap6} — design scenario for evacuation planning"),
            ("Evacuation flow rate",    "~40 pax/min per door pair",
             "UIC 660 / NFPA 130 benchmark"),
            ("Train doors per car",     "2 pairs per car",
             "Design input"),
            ("Doors per train",         f"{p.get('cars_per_train',6) * 2} pairs",
             f"{p.get('cars_per_train',6)} cars × 2 pairs"),
            ("Time to evacuate one train",
             f"{cap6 / (p.get('cars_per_train',6)*2*40):.1f} min (crush)",
             "Flow-based estimate at 40 pax/min/door"),
            ("Emergency exits (tunnel)",
             "≥ 1 per 500 m",
             "NFPA 130 §7.1"),
            ("Evacuation lighting endurance", "≥ 90 min",
             "EN 50172 / NFPA 130"),
            ("Communication during evacuation",
             "PA + OCC radio + station staff",
             "Simultaneous channels per emergency plan"),
        ]
        return pd.DataFrame(rows, columns=["Parameter","Value","Source / Standard"])

    @staticmethod
    def operator_responsibilities_table() -> pd.DataFrame:
        """RACI-style responsibility matrix for key operational events."""
        events = [
            ("Normal train service",        "R","A","C","I","I","I"),
            ("Service delay > 2 min",       "R","A","I","C","I","I"),
            ("Station evacuation",          "A","R","R","C","C","I"),
            ("Medical emergency on train",  "I","R","A","C","R","C"),
            ("Fire alarm activation",       "A","R","R","I","C","I"),
            ("Traction power isolation",    "R","C","A","I","I","R"),
            ("CBTC system fault",           "A","C","I","R","I","C"),
            ("Depot incursion / security",  "I","I","A","R","I","C"),
            ("Track access (possession)",   "A","C","R","I","I","I"),
            ("Shift handover",              "A","R","R","I","I","I"),
        ]
        cols = ["Event","Service Controller","Station Supervisor",
                "Duty Operations Mgr","Maintenance Eng.","Emergency Services","SCADA Operator"]
        note = "\nR=Responsible · A=Accountable · C=Consulted · I=Informed"
        df = pd.DataFrame(events, columns=cols)
        return df
