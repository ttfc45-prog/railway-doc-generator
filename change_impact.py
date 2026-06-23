"""
change_impact.py
Railway Documentation Generator — Change Impact Analysis Engine
===============================================================

analyze_change_impact(parameter_name, old_value, new_value, model, cs)

For any change to a ProjectModel input, identifies:
  • Which calculated parameters change (and by how much)
  • Which documents are affected
  • Which SRS requirements are affected
  • Severity of the change (critical / significant / minor / negligible)

This enables a railway engineer to immediately understand the cascade
effects of any design parameter change — without having to manually
trace through every calculation and document.

Example: v_max 80 → 90 km/h impacts:
  - headway.technical_headway_sec (braking time changes)
  - headway.minimum_safe_separation_m
  - ops.commercial_speed_kmh
  - ops.round_trip_time_min
  - ops.trains_in_service
  - ops.fleet_required
  - capacity.pphpd (via headway change if headway changes)
  - traction.peak_power_kw (F × v_max)
  - traction.energy_per_train_km_kwh
  - Documents: SRS, ConOps, HeadwayStudy, FleetCalc, TractionDesc
  - Requirements: SIG-REQ-0003, SYS-REQ-0005, SYS-REQ-0008
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import Any


# ═══════════════════════════════════════════════════════════════════════════════
# IMPACT STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ParameterChange:
    """A single calculated parameter that changes."""
    path:        str      # e.g. "ops.commercial_speed_kmh"
    description: str      # human-readable
    old_value:   float | int | str
    new_value:   float | int | str
    delta_abs:   float    # absolute change
    delta_pct:   float    # percentage change
    unit:        str
    severity:    str      # "critical" | "significant" | "minor" | "negligible"


@dataclass
class RequirementImpact:
    """An SRS/system requirement affected by the change."""
    req_id:      str
    description: str
    old_value:   str
    new_value:   str
    action:      str      # "update value" | "review validity" | "verify compliance"


@dataclass
class ImpactReport:
    """Complete impact analysis result."""
    parameter_name:         str
    old_value:              Any
    new_value:              Any
    unit:                   str
    severity:               str       # overall severity of the change
    summary:                str       # one-paragraph engineering summary

    changed_parameters:     list[ParameterChange]
    affected_documents:     list[str]
    affected_requirements:  list[RequirementImpact]
    unchanged_parameters:   list[str]  # key params that do NOT change

    delta_headway_sec:      float = 0.0   # change in technical headway (s)
    delta_fleet:            int   = 0     # change in fleet size
    delta_energy_pct:       float = 0.0   # % change in annual energy
    delta_pphpd:            int   = 0     # change in line capacity


# ═══════════════════════════════════════════════════════════════════════════════
# PARAMETER DEPENDENCY MAP
# ═══════════════════════════════════════════════════════════════════════════════

# Maps each input parameter to the calculation functions and downstream outputs it affects.
# Used to scope the re-calculation and impact assessment.

PARAM_DEPENDENCIES: dict[str, dict] = {
    "max_speed_kmh": {
        "affects_calculations": ["headway","operations","traction"],
        "key_outputs": ["headway.technical_headway_sec","headway.minimum_safe_separation_m",
                        "headway.braking_time_sec","ops.commercial_speed_kmh",
                        "traction.peak_power_kw","traction.energy_per_train_km_kwh"],
        "document_impact": ["SRS","ConOps","OCS","HeadwayStudy","FleetCalc","TractionDesc",
                            "EnergyMgmt","HazardLog","CapacityStudy","BOD","TechSpec"],
        "requirement_impact": ["SIG-REQ-0003","SYS-REQ-0005","SYS-REQ-0008","TEL-REQ-0001"],
    },
    "peak_headway_sec": {
        "affects_calculations": ["operations","capacity"],
        "key_outputs": ["ops.trains_in_service","ops.fleet_required","ops.total_fleet",
                        "ops.round_trip_time_min","capacity.pphpd_6ppm2",
                        "ops.daily_train_km","ops.annual_train_km"],
        "document_impact": ["ConOps","OCS","FleetCalc","CapacityStudy","SRS","HeadwayStudy",
                            "POP","BOD","ExecutiveSummary","EnergyMgmt"],
        "requirement_impact": ["SYS-REQ-0001","SYS-REQ-0002","SYS-REQ-0008"],
    },
    "number_of_stations": {
        "affects_calculations": ["operations","headway","traction"],
        "key_outputs": ["ops.commercial_speed_kmh","ops.running_time_min",
                        "traction.acc_energy_kwh_km","traction.energy_per_train_km_kwh"],
        "document_impact": ["ConOps","FleetCalc","HeadwayStudy","TractionDesc","EnergyMgmt"],
        "requirement_impact": ["SYS-REQ-0005"],
    },
    "line_length_km": {
        "affects_calculations": ["operations","traction","ram"],
        "key_outputs": ["ops.commercial_speed_kmh","ops.running_time_min","ops.round_trip_time_min",
                        "ops.daily_train_km","ops.annual_train_km","ram.km_between_failures",
                        "traction.annual_energy_mwh"],
        "document_impact": ["ConOps","FleetCalc","HeadwayStudy","RAM","EnergyMgmt","BOD","TechSpec"],
        "requirement_impact": ["SYS-REQ-0005","RA-004"],
    },
    "emergency_deceleration_mss": {
        "affects_calculations": ["headway"],
        "key_outputs": ["headway.technical_headway_sec","headway.minimum_safe_separation_m",
                        "headway.braking_distance_m","headway.braking_time_sec"],
        "document_impact": ["SRS","HeadwayStudy","HazardLog","ConOps","OCS","SafetyCase"],
        "requirement_impact": ["SIG-REQ-0003"],
    },
    "mtbf_target_hours": {
        "affects_calculations": ["ram","rams_allocation"],
        "key_outputs": ["ram.availability","ram.mission_reliability_24h",
                        "ram.km_between_failures","rams_alloc.series_mtbf_hours",
                        "rams_alloc.allocated_mtbf_hours"],
        "document_impact": ["RAM","Reliability","Availability","Maintainability",
                            "SRS","MaintenancePlan","SafetyCase","TechSpec"],
        "requirement_impact": ["SYS-REQ-0003","RA-001","RA-002","RA-004"],
    },
    "mttr_target_hours": {
        "affects_calculations": ["ram","rams_allocation"],
        "key_outputs": ["ram.availability","ram.maintainability_8h",
                        "rams_alloc.allocated_avail_pct","rams_alloc.series_avail_pct"],
        "document_impact": ["RAM","Maintainability","Availability","MaintenancePlan"],
        "requirement_impact": ["SYS-REQ-0003","RA-003"],
    },
    "cars_per_train": {
        "affects_calculations": ["traction","capacity"],
        "key_outputs": ["traction.train_mass_tonnes","traction.peak_power_kw",
                        "traction.energy_per_train_km_kwh","traction.annual_energy_mwh",
                        "traction.substation_rating_mva","traction.auxiliary_energy_kwh_km"],
        "document_impact": ["ConOps","FleetCalc","TractionDesc","EnergyMgmt","BOD","SRS","TechSpec"],
        "requirement_impact": ["SYS-REQ-0008","TR-001","TR-002","TR-004","TR-005"],
    },
    "seated_capacity": {
        "affects_calculations": ["capacity"],
        "key_outputs": ["capacity.capacity_4ppm2","capacity.capacity_6ppm2",
                        "capacity.pphpd_4ppm2","capacity.pphpd_6ppm2",
                        "capacity.load_factor_4ppm2_pct","capacity.load_factor_6ppm2_pct"],
        "document_impact": ["ConOps","CapacityStudy","SRS","HumanFactors"],
        "requirement_impact": ["SYS-REQ-0001"],
    },
    "standing_capacity_6ppm2": {
        "affects_calculations": ["capacity"],
        "key_outputs": ["capacity.capacity_6ppm2","capacity.pphpd_6ppm2",
                        "capacity.load_factor_6ppm2_pct","capacity.capacity_adequate"],
        "document_impact": ["ConOps","CapacityStudy","SRS","HumanFactors","BOD"],
        "requirement_impact": ["SYS-REQ-0001","CA-002"],
    },
    "peak_demand_pphpd": {
        "affects_calculations": ["capacity"],
        "key_outputs": ["capacity.demand_pphpd","capacity.load_factor_4ppm2_pct",
                        "capacity.load_factor_6ppm2_pct","capacity.capacity_adequate"],
        "document_impact": ["ConOps","CapacityStudy","SRS","BOD","POP"],
        "requirement_impact": ["SYS-REQ-0001"],
    },
    "number_of_substations": {
        "affects_calculations": ["traction"],
        "key_outputs": ["traction.substation_rating_mva"],
        "document_impact": ["TractionDesc","EnergyMgmt","BOD","TechSpec"],
        "requirement_impact": ["TR-005"],
    },
    "regen_recoverable_fraction": {
        "affects_calculations": ["traction"],
        "key_outputs": ["traction.regenerative_saving_pct","traction.braking_energy_kwh_km",
                        "traction.energy_per_train_km_kwh","traction.annual_energy_mwh"],
        "document_impact": ["TractionDesc","EnergyMgmt","BOD"],
        "requirement_impact": ["TR-003","TR-004"],
    },
    "station_dwell_sec": {
        "affects_calculations": ["headway","operations"],
        "key_outputs": ["headway.commercial_headway_sec","ops.running_time_min",
                        "ops.round_trip_time_min","ops.trains_in_service",
                        "ops.fleet_required"],
        "document_impact": ["ConOps","HeadwayStudy","FleetCalc","POP","OCS"],
        "requirement_impact": ["SYS-REQ-0002","SYS-REQ-0008"],
    },
    "operating_hours_per_day": {
        "affects_calculations": ["operations"],
        "key_outputs": ["ops.daily_train_km","ops.annual_train_km","traction.annual_energy_mwh"],
        "document_impact": ["ConOps","EnergyMgmt","MaintenancePlan","POP"],
        "requirement_impact": [],
    },
    "max_acceleration_mss": {
        "affects_calculations": ["operations","traction"],
        "key_outputs": ["ops.commercial_speed_kmh","ops.running_time_min",
                        "ops.acc_distance_m","traction.peak_power_kw",
                        "traction.acc_energy_kwh_km"],
        "document_impact": ["ConOps","FleetCalc","TractionDesc","EnergyMgmt","TechSpec"],
        "requirement_impact": ["SYS-REQ-0005","TR-001"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# IMPACT ANALYSER
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_change_impact(
    parameter_name: str,
    old_value: Any,
    new_value: Any,
    model,
    cs,
) -> ImpactReport:
    """
    Analyse the engineering impact of changing a single ProjectModel input.

    Steps:
      1. Create a modified copy of the project inputs
      2. Re-run CalculationEngine with new value
      3. Compare CalculatedState before and after
      4. Map changed parameters to affected documents and requirements
      5. Generate a narrative engineering summary

    Parameters
    ----------
    parameter_name : str
        The ProjectModel input key to change (e.g. "max_speed_kmh")
    old_value : Any
        The current value (used to compute delta and for context)
    new_value : Any
        The proposed new value
    model : ProjectModel
        The current project model
    cs : CalculatedState
        The current calculated state (pre-change)

    Returns
    -------
    ImpactReport
        Fully populated impact report
    """
    from calculations import CalculationEngine
    from project_model import ProjectModel

    # Build modified model
    new_inputs = {k: v for k, v in model.to_dict().items()
                  if k not in ProjectModel._FORBIDDEN_KEYS}
    new_inputs[parameter_name] = new_value

    try:
        new_model = ProjectModel(new_inputs)
        new_cs    = CalculationEngine.run(new_model)
    except Exception as e:
        return ImpactReport(
            parameter_name=parameter_name, old_value=old_value, new_value=new_value,
            unit="", severity="ERROR", summary=f"Could not re-calculate: {e}",
            changed_parameters=[], affected_documents=[],
            affected_requirements=[], unchanged_parameters=[],
        )

    # Get dependency info for this parameter
    dep_info = PARAM_DEPENDENCIES.get(parameter_name, {
        "affects_calculations": ["operations","headway","capacity","ram","traction","rams_allocation"],
        "key_outputs": [],
        "document_impact": list({k for d in PARAM_DEPENDENCIES.values()
                                  for k in d.get("document_impact",[])}),
        "requirement_impact": [],
    })

    # ── Compare CalculatedStates ──────────────────────────────────────────────
    changed: list[ParameterChange] = []
    unchanged: list[str] = []

    def _delta(old, new, path, desc, unit, crit_threshold_pct=5.0):
        try:
            old_f = float(old); new_f = float(new)
            d_abs = new_f - old_f
            d_pct = (d_abs / abs(old_f) * 100.0) if old_f != 0 else float("inf")
            if abs(d_pct) < 0.001:
                unchanged.append(f"{path} = {old_f}")
                return None
            sev = ("critical" if abs(d_pct) >= crit_threshold_pct
                   else "significant" if abs(d_pct) >= 1.0
                   else "minor" if abs(d_pct) >= 0.1
                   else "negligible")
            return ParameterChange(path, desc, old_f, new_f, round(d_abs,4),
                                   round(d_pct,3), unit, sev)
        except (TypeError, ValueError):
            if str(old) != str(new):
                return ParameterChange(path, desc, old, new, 0, 0, unit, "significant")
            return None

    checks = [
        ("ops.commercial_speed_kmh", "Commercial Speed",
         cs.ops.commercial_speed_kmh, new_cs.ops.commercial_speed_kmh, "km/h"),
        ("ops.running_time_min", "One-way Running Time",
         cs.ops.running_time_min, new_cs.ops.running_time_min, "min"),
        ("ops.round_trip_time_min", "Round Trip Time",
         cs.ops.round_trip_time_min, new_cs.ops.round_trip_time_min, "min"),
        ("ops.trains_in_service", "Trains in Service",
         cs.ops.trains_in_service, new_cs.ops.trains_in_service, "trains"),
        ("ops.fleet_required", "Operational Fleet",
         cs.ops.fleet_required, new_cs.ops.fleet_required, "trains"),
        ("ops.reserve_trains", "Reserve Fleet",
         cs.ops.reserve_trains, new_cs.ops.reserve_trains, "trains"),
        ("ops.total_fleet", "Total Fleet",
         cs.ops.total_fleet, new_cs.ops.total_fleet, "trains"),
        ("ops.daily_train_km", "Daily Train-km",
         cs.ops.daily_train_km, new_cs.ops.daily_train_km, "km"),
        ("ops.annual_train_km", "Annual Train-km",
         cs.ops.annual_train_km, new_cs.ops.annual_train_km, "km"),
        ("headway.technical_headway_sec", "Technical Headway",
         cs.headway.technical_headway_sec, new_cs.headway.technical_headway_sec, "s"),
        ("headway.commercial_headway_sec", "Commercial Headway",
         cs.headway.commercial_headway_sec, new_cs.headway.commercial_headway_sec, "s"),
        ("headway.minimum_safe_separation_m", "Min Safe Separation",
         cs.headway.minimum_safe_separation_m, new_cs.headway.minimum_safe_separation_m, "m"),
        ("headway.braking_distance_m", "Braking Distance",
         cs.headway.braking_distance_m, new_cs.headway.braking_distance_m, "m"),
        ("headway.braking_time_sec", "Braking Time",
         cs.headway.braking_time_sec, new_cs.headway.braking_time_sec, "s"),
        ("capacity.pphpd_6ppm2", "Line Capacity PPHPD",
         cs.capacity.pphpd_6ppm2, new_cs.capacity.pphpd_6ppm2, "pphpd"),
        ("capacity.capacity_6ppm2", "Train Capacity (6 pax/m²)",
         cs.capacity.capacity_6ppm2, new_cs.capacity.capacity_6ppm2, "pax"),
        ("capacity.load_factor_6ppm2_pct", "Load Factor",
         cs.capacity.load_factor_6ppm2_pct, new_cs.capacity.load_factor_6ppm2_pct, "%"),
        ("ram.availability", "System Availability",
         cs.ram.availability*100, new_cs.ram.availability*100, "%"),
        ("ram.km_between_failures", "km Between Failures",
         cs.ram.km_between_failures, new_cs.ram.km_between_failures, "km"),
        ("traction.peak_power_kw", "Peak Tractive Power",
         cs.traction.peak_power_kw, new_cs.traction.peak_power_kw, "kW"),
        ("traction.energy_per_train_km_kwh", "Net Energy/Train-km",
         cs.traction.energy_per_train_km_kwh, new_cs.traction.energy_per_train_km_kwh, "kWh/km"),
        ("traction.regenerative_saving_pct", "Regen Saving",
         cs.traction.regenerative_saving_pct, new_cs.traction.regenerative_saving_pct, "%"),
        ("traction.substation_rating_mva", "Substation Rating",
         cs.traction.substation_rating_mva, new_cs.traction.substation_rating_mva, "MVA"),
        ("traction.annual_energy_mwh", "Annual Energy",
         cs.traction.annual_energy_mwh, new_cs.traction.annual_energy_mwh, "MWh"),
        ("rams_alloc.series_mtbf_hours", "Series MTBF",
         cs.rams_alloc.series_mtbf_hours, new_cs.rams_alloc.series_mtbf_hours, "h"),
        ("rams_alloc.series_avail_pct", "Series Availability",
         cs.rams_alloc.series_avail_pct, new_cs.rams_alloc.series_avail_pct, "%"),
    ]

    for path, desc, old, new, unit in checks:
        c = _delta(old, new, path, desc, unit)
        if c:
            changed.append(c)

    # ── Delta shortcuts ───────────────────────────────────────────────────────
    delta_headway = (new_cs.headway.technical_headway_sec -
                     cs.headway.technical_headway_sec)
    delta_fleet   = new_cs.ops.total_fleet - cs.ops.total_fleet
    delta_pphpd   = new_cs.capacity.pphpd_6ppm2 - cs.capacity.pphpd_6ppm2
    old_e = cs.traction.annual_energy_mwh
    new_e = new_cs.traction.annual_energy_mwh
    delta_energy_pct = (new_e - old_e) / old_e * 100.0 if old_e else 0.0

    # ── Overall severity ─────────────────────────────────────────────────────
    sev_order = {"critical":0,"significant":1,"minor":2,"negligible":3}
    if not changed:
        overall_sev = "negligible"
    else:
        worst = min(changed, key=lambda c: sev_order.get(c.severity, 4))
        overall_sev = worst.severity

    # ── Affected requirements ─────────────────────────────────────────────────
    req_impacts: list[RequirementImpact] = []
    if "SIG-REQ-0003" in dep_info.get("requirement_impact", []):
        req_impacts.append(RequirementImpact(
            req_id="SIG-REQ-0003",
            description="The ATC system shall achieve a technical headway not exceeding X s",
            old_value=f"{cs.headway.technical_headway_sec:.1f} s",
            new_value=f"{new_cs.headway.technical_headway_sec:.1f} s",
            action="update value" if abs(delta_headway) > 0.01 else "review validity",
        ))
    if "SYS-REQ-0005" in dep_info.get("requirement_impact", []):
        req_impacts.append(RequirementImpact(
            req_id="SYS-REQ-0005",
            description="Commercial speed shall be not less than X km/h",
            old_value=f"{cs.ops.commercial_speed_kmh:.1f} km/h",
            new_value=f"{new_cs.ops.commercial_speed_kmh:.1f} km/h",
            action="update value" if abs(
                new_cs.ops.commercial_speed_kmh - cs.ops.commercial_speed_kmh) > 0.01
                else "review validity",
        ))
    if "SYS-REQ-0008" in dep_info.get("requirement_impact", []):
        req_impacts.append(RequirementImpact(
            req_id="SYS-REQ-0008",
            description=f"Operational fleet shall consist of not fewer than X trains",
            old_value=f"{cs.ops.fleet_required} trains",
            new_value=f"{new_cs.ops.fleet_required} trains",
            action="update value" if delta_fleet != 0 else "review validity",
        ))
    if "SYS-REQ-0001" in dep_info.get("requirement_impact", []):
        req_impacts.append(RequirementImpact(
            req_id="SYS-REQ-0001",
            description=f"System shall achieve ≥ {cs.capacity.demand_pphpd:,} pphpd",
            old_value=f"{cs.capacity.pphpd_6ppm2:,} pphpd",
            new_value=f"{new_cs.capacity.pphpd_6ppm2:,} pphpd",
            action=("URGENT — capacity below demand"
                    if not new_cs.capacity.capacity_adequate else "review validity"),
        ))
    if "SYS-REQ-0003" in dep_info.get("requirement_impact", []):
        old_a = cs.ram.availability * 100
        new_a = new_cs.ram.availability * 100
        req_impacts.append(RequirementImpact(
            req_id="SYS-REQ-0003",
            description="System availability shall be not less than X%",
            old_value=f"{old_a:.4f}%",
            new_value=f"{new_a:.4f}%",
            action="review validity",
        ))

    # ── Summary narrative ─────────────────────────────────────────────────────
    param_label = parameter_name.replace("_"," ")
    try:
        delta_v = float(new_value) - float(old_value)
        delta_pct_v = delta_v / float(old_value) * 100 if float(old_value) != 0 else 0
        delta_str = (f"+{delta_v:.2f}" if delta_v >= 0 else f"{delta_v:.2f}")
        pct_str   = (f"+{delta_pct_v:.1f}%" if delta_pct_v >= 0 else f"{delta_pct_v:.1f}%")
    except (TypeError, ValueError):
        delta_str = f"{old_value} → {new_value}"
        pct_str   = ""

    changed_names = [c.description for c in changed if c.severity in ("critical","significant")]
    summary = (
        f"Changing {param_label} from {old_value} to {new_value} "
        f"({delta_str}{', ' + pct_str if pct_str else ''}) "
        f"produces a {overall_sev} change to the CalculatedState. "
    )
    if changed_names:
        summary += (
            f"The most significant effects are on: {', '.join(changed_names[:5])}. "
        )
    if delta_fleet != 0:
        summary += (
            f"Fleet size changes by {delta_fleet:+d} trains "
            f"({cs.ops.total_fleet} → {new_cs.ops.total_fleet}). "
        )
    if abs(delta_headway) > 0.1:
        summary += (
            f"Technical headway changes by {delta_headway:+.1f} s "
            f"({cs.headway.technical_headway_sec:.1f} → {new_cs.headway.technical_headway_sec:.1f} s), "
            f"requiring SRS SIG-REQ-0003 to be updated. "
        )
    if abs(delta_energy_pct) > 1.0:
        summary += (
            f"Annual energy changes by {delta_energy_pct:+.1f}% "
            f"({cs.traction.annual_energy_mwh:,.0f} → {new_cs.traction.annual_energy_mwh:,.0f} MWh/year). "
        )
    if not cs.capacity.capacity_adequate and new_cs.capacity.capacity_adequate:
        summary += "Capacity constraint is RESOLVED by this change. "
    elif cs.capacity.capacity_adequate and not new_cs.capacity.capacity_adequate:
        summary += "WARNING: This change causes line capacity to fall BELOW peak demand. "
    if len(changed) == 0:
        summary += "No calculated parameters are materially affected by this change."

    return ImpactReport(
        parameter_name          = parameter_name,
        old_value               = old_value,
        new_value               = new_value,
        unit                    = "",
        severity                = overall_sev,
        summary                 = summary,
        changed_parameters      = sorted(changed, key=lambda c: {"critical":0,"significant":1,
                                                                   "minor":2,"negligible":3}
                                                                  .get(c.severity,4)),
        affected_documents      = dep_info.get("document_impact", []),
        affected_requirements   = req_impacts,
        unchanged_parameters    = unchanged[:10],
        delta_headway_sec       = delta_headway,
        delta_fleet             = delta_fleet,
        delta_energy_pct        = delta_energy_pct,
        delta_pphpd             = delta_pphpd,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# HTML REPORT RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_impact_html(report: ImpactReport) -> str:
    """Render an ImpactReport as self-contained HTML."""
    SEV_STYLE = {
        "critical":    ("🔴","#FDECEA","#C0392B"),
        "significant": ("🟠","#FEF9E7","#E67E22"),
        "minor":       ("🔵","#EBF5FB","#2980B9"),
        "negligible":  ("🟢","#EAFAF1","#27AE60"),
        "ERROR":       ("❌","#FDECEA","#C0392B"),
    }
    icon, bg, colour = SEV_STYLE.get(report.severity, ("⚪","#F8F9FA","#555"))

    param_rows = ""
    for c in report.changed_parameters:
        i2, bg2, col2 = SEV_STYLE.get(c.severity,("⚪","#F8F9FA","#555"))
        sign = "+" if c.delta_pct > 0 else ""
        param_rows += f"""<tr>
          <td style='padding:7px 12px;border-bottom:1px solid #E5E7EB;font-size:12.5px'>{c.description}</td>
          <td style='padding:7px 12px;border-bottom:1px solid #E5E7EB;font-family:monospace;font-size:12px'>{c.old_value} {c.unit}</td>
          <td style='padding:7px 12px;border-bottom:1px solid #E5E7EB;font-family:monospace;font-size:12px'>{c.new_value} {c.unit}</td>
          <td style='padding:7px 12px;border-bottom:1px solid #E5E7EB;font-family:monospace;font-size:12px;color:{col2}'>{sign}{c.delta_pct:.2f}%</td>
          <td style='padding:7px 12px;border-bottom:1px solid #E5E7EB'><span style='background:{bg2};color:{col2};padding:2px 7px;border-radius:3px;font-size:10px;font-weight:800'>{c.severity.upper()}</span></td>
        </tr>"""

    req_rows = ""
    for r in report.affected_requirements:
        req_rows += f"""<tr>
          <td style='padding:6px 12px;border-bottom:1px solid #E5E7EB;font-weight:700;color:#003087'>{r.req_id}</td>
          <td style='padding:6px 12px;border-bottom:1px solid #E5E7EB;font-size:12px'>{r.description}</td>
          <td style='padding:6px 12px;border-bottom:1px solid #E5E7EB;font-family:monospace;font-size:11px'>{r.old_value}</td>
          <td style='padding:6px 12px;border-bottom:1px solid #E5E7EB;font-family:monospace;font-size:11px'>{r.new_value}</td>
          <td style='padding:6px 12px;border-bottom:1px solid #E5E7EB;font-size:11px;color:#C0392B'>{r.action}</td>
        </tr>"""

    docs_html = "".join(
        f'<span style="background:#EAF0FB;color:#003087;padding:3px 8px;border-radius:3px;'
        f'font-size:11px;margin:2px;display:inline-block">{d}</span>'
        for d in report.affected_documents
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8">
<title>Change Impact: {report.parameter_name}</title>
<style>
  body {{font-family:"Segoe UI",Arial,sans-serif;margin:0;background:#fff;color:#1B2631;font-size:13px}}
  table {{border-collapse:collapse;width:100%}}
  th {{background:#003087;color:#fff;padding:8px 12px;text-align:left;font-size:11px;letter-spacing:.06em;text-transform:uppercase}}
  .hdr {{background:#003087;color:#fff;padding:24px 36px;border-bottom:4px solid #C0392B}}
  .sec {{padding:16px 36px}}
  .sec h2 {{font-size:14px;font-weight:800;color:#003087;border-bottom:2px solid #003087;padding-bottom:5px;margin:20px 0 10px}}
</style>
</head>
<body>
<div class="hdr">
  <div style="font-size:10px;letter-spacing:.18em;text-transform:uppercase;opacity:.6;margin-bottom:4px">Change Impact Analysis</div>
  <h1 style="font-size:20px;font-weight:800;margin:0 0 6px">{icon} {report.parameter_name}: {report.old_value} → {report.new_value}</h1>
  <div style="font-size:12px;opacity:.7">Overall Severity: <strong>{report.severity.upper()}</strong> &nbsp;|&nbsp; {len(report.changed_parameters)} parameters affected &nbsp;|&nbsp; {len(report.affected_documents)} documents</div>
</div>

<div class="sec">
  <h2>Engineering Summary</h2>
  <div style="background:{bg};border-left:4px solid {colour};padding:14px 18px;border-radius:0 6px 6px 0;font-size:13.5px;line-height:1.6">
    {report.summary}
  </div>
</div>

<div class="sec">
  <h2>Changed Calculated Parameters ({len(report.changed_parameters)})</h2>
  <table>
    <thead><tr><th>Parameter</th><th>Before</th><th>After</th><th>Change %</th><th>Severity</th></tr></thead>
    <tbody>{param_rows if param_rows else '<tr><td colspan="5" style="padding:12px;color:#888;text-align:center">No calculated parameters changed materially.</td></tr>'}</tbody>
  </table>
</div>

<div class="sec">
  <h2>Affected Requirements ({len(report.affected_requirements)})</h2>
  <table>
    <thead><tr><th>Req. ID</th><th>Description</th><th>Old Value</th><th>New Value</th><th>Required Action</th></tr></thead>
    <tbody>{req_rows if req_rows else '<tr><td colspan="5" style="padding:12px;color:#888;text-align:center">No requirements directly affected.</td></tr>'}</tbody>
  </table>
</div>

<div class="sec">
  <h2>Affected Documents ({len(report.affected_documents)})</h2>
  <div style="margin-top:8px">{docs_html}</div>
</div>

<div class="sec" style="color:#888;font-size:11px;border-top:1px solid #E5E7EB;padding-top:12px">
  Railway Documentation Generator — Change Impact Analysis Engine &nbsp;|&nbsp;
  All values from CalculationEngine (deterministic)
</div>
</body></html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# STREAMLIT UI
# ═══════════════════════════════════════════════════════════════════════════════

def render_impact_tab(model, cs) -> None:
    """Render the Change Impact Analysis UI inside a Streamlit tab."""
    import streamlit as st
    import pandas as pd

    st.markdown("### Change Impact Analysis Engine")
    st.caption(
        "Select any ProjectModel input, propose a new value, and immediately see "
        "all affected calculated parameters, documents and SRS requirements."
    )

    analysable = sorted(PARAM_DEPENDENCIES.keys())
    param_labels = {k: k.replace("_", " ").title() for k in analysable}

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        selected = st.selectbox(
            "Parameter to change",
            options=analysable,
            format_func=lambda k: f"{param_labels[k]}  ({k})",
        )
    current_val = model.get(selected)
    with col2:
        st.metric("Current value", str(current_val))
    with col3:
        try:
            new_val = st.number_input(
                "Proposed value",
                value=float(current_val),
                step=float(current_val) * 0.05 if float(current_val) > 0 else 1.0,
                format="%.4f",
            )
        except (TypeError, ValueError):
            new_val = st.text_input("Proposed value", value=str(current_val))

    if st.button("▶  Analyse Change Impact", type="primary", use_container_width=True):
        if str(new_val) == str(current_val):
            st.info("Proposed value equals current value — no change to analyse.")
            return

        with st.spinner("Re-running CalculationEngine with new value…"):
            report = analyze_change_impact(selected, current_val, new_val, model, cs)

        SEV_COLOUR = {"critical":"#FDECEA","significant":"#FEF9E7",
                      "minor":"#EBF5FB","negligible":"#EAFAF1","ERROR":"#FDECEA"}
        SEV_BORDER = {"critical":"#C0392B","significant":"#E67E22",
                      "minor":"#2980B9","negligible":"#27AE60","ERROR":"#C0392B"}
        bg = SEV_COLOUR.get(report.severity,"#F8F9FA")
        bc = SEV_BORDER.get(report.severity,"#888")

        st.markdown(
            f"<div style='background:{bg};border-left:5px solid {bc};"
            f"padding:14px 18px;border-radius:0 6px 6px 0;margin-bottom:16px'>"
            f"<div style='font-size:11px;font-weight:800;letter-spacing:.1em;"
            f"text-transform:uppercase;color:{bc};margin-bottom:4px'>"
            f"Overall: {report.severity.upper()}</div>"
            f"<div style='font-size:13.5px;line-height:1.6'>{report.summary}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # KPI deltas
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Headway Δ",
                  f"{report.delta_headway_sec:+.1f} s",
                  delta_color="inverse" if report.delta_headway_sec > 0 else "normal")
        c2.metric("Fleet Δ",
                  f"{report.delta_fleet:+d} trains",
                  delta_color="inverse" if report.delta_fleet > 0 else "normal")
        c3.metric("PPHPD Δ",
                  f"{report.delta_pphpd:+,}",
                  delta_color="normal" if report.delta_pphpd > 0 else "inverse")
        c4.metric("Energy Δ",
                  f"{report.delta_energy_pct:+.1f}%",
                  delta_color="inverse" if report.delta_energy_pct > 0 else "normal")

        # Changed parameters table
        if report.changed_parameters:
            st.markdown("#### Changed Calculated Parameters")
            rows = []
            for c in report.changed_parameters:
                sign = "+" if c.delta_pct > 0 else ""
                rows.append({"Parameter":    c.description,
                              "Before":       f"{c.old_value} {c.unit}",
                              "After":        f"{c.new_value} {c.unit}",
                              "Δ %":          f"{sign}{c.delta_pct:.3f}%",
                              "Severity":     c.severity.upper()})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Affected requirements
        if report.affected_requirements:
            st.markdown("#### Affected SRS Requirements")
            rows = []
            for r in report.affected_requirements:
                rows.append({"ID":r.req_id,"Description":r.description[:60],
                             "Before":r.old_value,"After":r.new_value,"Action":r.action})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Affected documents
        st.markdown("#### Affected Documents")
        doc_cols = st.columns(min(6, len(report.affected_documents)))
        for i, doc in enumerate(report.affected_documents):
            doc_cols[i % len(doc_cols)].info(doc)

        # Download HTML report
        html = render_impact_html(report)
        st.download_button(
            "⬇  Download Impact Report (HTML)",
            data=html,
            file_name=f"ChangeImpact_{selected}_{current_val}_to_{new_val}.html",
            mime="text/html",
            use_container_width=True,
        )
