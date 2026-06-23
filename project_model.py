"""
project_model.py
Railway Documentation Generator — ProjectModel
===============================================

CANONICAL USER-INPUT DEFINITION.

This module contains the single authoritative definition of every primitive
input that a user may provide to the system.  It contains NO derived or
calculated values.  Commercial speed, technical headway, fleet size, km
between failures, energy per km — none of these belong here.

Design rules (enforced by the class itself):
  • Every field is a primitive Python type (str, int, float, bool, list[str]).
  • No field may be a result of any formula.
  • Validation is strict: invalid inputs raise ValueError immediately.
  • The class is JSON-serialisable (to_dict / from_dict).
  • DEFAULT_INPUTS is the factory preset — no assumptions about derived values.

Separation from CalculatedState (calculations.py) is absolute:
  • ProjectModel → CalculationEngine → CalculatedState
  • Nothing flows in the opposite direction.
"""

from __future__ import annotations

import json
import copy
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# ═══════════════════════════════════════════════════════════════════════════════
# DEFAULT INPUT VALUES (primitives only — no derived quantities)
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_INPUTS: dict[str, Any] = {
    # ── Project Identity ─────────────────────────────────────────────────────
    "project_name":          "Metro Line X",
    "country":               "Brazil",
    "client":                "State Metro Authority",
    "consultant":            "Railway Engineering Consultants",
    "document_number":       "RDG-BOD-001",
    "revision":              "A",
    "status":                "For Review",
    "project_life_years":    40,
    "warranty_years":        2,

    # ── Geometry (user-measured / surveyed) ──────────────────────────────────
    "line_name":             "Line X",
    "line_length_km":        22.5,
    "number_of_stations":    18,
    "depot_location":        "Northern Terminal",
    "number_of_tracks":      2,
    "track_gauge_mm":        1435,
    "loading_gauge":         "UIC 505-1",

    # ── Operating Pattern (user-specified service plan) ───────────────────────
    "max_speed_kmh":             80,      # design maximum speed — NOT commercial speed
    "design_speed_kmh":          90,      # structural design speed
    "operating_hours_per_day":   18,
    "peak_hours_per_day":        4,
    "off_peak_hours_per_day":    14,
    "peak_headway_sec":          90,      # service interval: 90s needed for 45,000 pphpd at 1,224 pax/train
    "off_peak_headway_sec":      180,     # off-peak: every 3 minutes
    "terminal_dwell_min":        3.0,     # layover at each terminal
    "station_dwell_sec":         35,      # passenger boarding/alighting dwell

    # ── Demand Forecasts (from external demand model) ─────────────────────────
    "peak_demand_pphpd":         45000,
    "daily_passengers":          500000,
    "annual_passengers":         180000000,

    # ── Rolling Stock (physical and contractual specifications) ───────────────
    "cars_per_train":            6,
    "train_length_m":            138.0,
    "train_width_m":             2.88,
    "train_height_m":            3.70,
    "seated_capacity":           306,     # seats per trainset
    "standing_capacity_4ppm2":   612,     # standing at 4 pax/m²
    "standing_capacity_6ppm2":   918,     # standing at 6 pax/m² (crush)
    "max_acceleration_mss":      1.0,     # m/s² service acceleration
    "max_deceleration_mss":      1.0,     # m/s² service braking
    "emergency_deceleration_mss":1.3,     # m/s² emergency braking
    "mass_per_car_tonnes":       40.0,    # AW3 loading per car

    # ── Operational Performance Targets (user / client requirements) ──────────
    "operational_availability_target_pct": 98.0,   # fleet availability for service
    "reserve_fleet_pct":                   10.0,   # reserve as % of operational fleet

    # ── Signalling (system type and configuration) ────────────────────────────
    "signalling_system":         "CBTC Moving Block",
    "goa_level":                 "GOA4 (UTO)",
    "atc_vendor":                "TBD",
    "safety_integrity_level":    "SIL 4",

    # ── Power Supply (configuration inputs) ──────────────────────────────────
    "power_supply_voltage":      "1500 Vdc",
    "power_supply_type":         "Overhead Catenary System (OCS)",
    "substation_spacing_km":     2.5,
    "number_of_substations":     10,
    "regenerative_braking":      True,
    "regen_recovery_efficiency": 0.70,    # regeneration chain efficiency (0–1)
    "regen_recoverable_fraction":0.30,    # fraction of braking energy recoverable
    "mean_gradient_permille":    0.0,     # mean route gradient (‰) — 0 for flat metro
    "auxiliary_power_kw_per_car":15.0,    # auxiliary (hotel) load per car: HVAC+lighting+electronics (kW)

    # ── RAMS Targets (client / regulatory requirements) ───────────────────────
    "system_availability_target_pct":      99.5,
    "operational_availability_target_pct": 98.0,
    "mtbf_target_hours":                   50000,
    "mttr_target_hours":                   4.0,
    "reliability_target_km":               200000,

    # ── Telecommunications (system selection) ─────────────────────────────────
    "telecom_systems": [
        "TETRA Radio", "CCTV", "Public Address",
        "Passenger Information System", "Clocks",
        "Telephone Network", "SCADA Communication",
    ],
    "scada_system":              "Centralised SCADA with distributed RTUs",
    "scada_poll_interval_sec":   2,

    # ── Environmental Conditions (site-specific data) ─────────────────────────
    "ambient_temp_min_c":        -5,
    "ambient_temp_max_c":        45,
    "humidity_max_pct":          95,
    "altitude_max_m":            900,
    "seismic_zone":              "Zone 2B",
    "ip_rating_tunnels":         "IP54",
    "ip_rating_outdoor":         "IP65",

    # ── Applicable Standards (project selection) ──────────────────────────────
    "design_standards": [
        "EN 50126 (RAMS)", "EN 50128 (Software)", "EN 50129 (Safety)",
        "EN 50159 (Communication)", "EN 62290 (CBTC)", "IEC 62267 (GoA)",
        "NFPA 130 (Fire)", "UIC 505-1 (Loading Gauge)", "EN 15227 (Crashworthiness)",
    ],

    # ── Depot & Maintenance (operational configuration) ───────────────────────
    "maintenance_regime":        "Preventive and Corrective",
    "maintenance_window_hours":  6,
    "cmms_system":               "IBM Maximo",

    # ── Platform Screen Doors ────────────────────────────────────────────────
    "psd_type":                  "Full-Height PSD",
    "psd_door_width_m":          1.8,
    "psd_door_height_m":         2.1,
    "psd_cycle_time_sec":        8,
    "psd_sil_level":             "SIL 2",

    # ── Stations ─────────────────────────────────────────────────────────────
    "station_list":              [],      # populated by user in UI
}


# ═══════════════════════════════════════════════════════════════════════════════
# PROJECTMODEL
# ═══════════════════════════════════════════════════════════════════════════════

class ProjectModel:
    """
    Validated container for all user-provided primitive inputs.

    Invariants:
      • Stores ONLY inputs — never calculated outputs.
      • Raises ValueError on invalid inputs (not silently corrected).
      • Serialises cleanly to/from JSON for persistence.
      • Provides a .to_dict() → dict for passing to CalculationEngine.
    """

    # Fields that are FORBIDDEN from being stored (calculated outputs)
    _FORBIDDEN_KEYS: frozenset[str] = frozenset({
        "commercial_speed_kmh",
        "technical_headway_sec",
        "fleet_size",
        "total_fleet",
        "fleet_required",
        "reserve_trains",
        "daily_train_km",
        "annual_train_km",
        "round_trip_time_min",
        "running_time_min",
        "km_between_failures",
        "energy_kwh_per_km",
        "energy_per_train_km_kwh",
        "regenerative_saving_pct",
        "pphpd_4ppm2",
        "pphpd_6ppm2",
        "capacity_train_4ppm2",
        "capacity_train_6ppm2",
        "total_capacity_6ppm2",
        "total_capacity_4ppm2",
        "system_availability",
        "availability_predicted",
        "mtbf_calculated",
        "headway_technical_sec",
        "headway_commercial_sec",
        "trains_in_service",
    })

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data: dict[str, Any] = copy.deepcopy(DEFAULT_INPUTS)
        if data:
            self._apply(data)

    # ── Internal application with forbidden-key guard ─────────────────────────

    def _apply(self, data: dict[str, Any]) -> None:
        forbidden_found = [k for k in data if k in self._FORBIDDEN_KEYS]
        if forbidden_found:
            raise ValueError(
                f"ProjectModel received calculated output(s) as input — forbidden: "
                f"{forbidden_found}. These values must never be stored; they are "
                f"always computed by CalculationEngine."
            )
        self._data.update(data)

    # ── Public getters ────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        """Return a deep copy of all inputs as a plain dict."""
        return copy.deepcopy(self._data)

    # ── Setters (with forbidden-key enforcement) ──────────────────────────────

    def set(self, key: str, value: Any) -> None:
        if key in self._FORBIDDEN_KEYS:
            raise ValueError(
                f"Cannot store '{key}' in ProjectModel — it is a calculated output. "
                f"Read it from CalculatedState instead."
            )
        self._data[key] = value

    def update(self, data: dict[str, Any]) -> None:
        self._apply(data)

    # ── Validation ────────────────────────────────────────────────────────────

    def validate(self) -> list[str]:
        """
        Run all consistency checks. Returns a list of error messages.
        Empty list → model is valid.
        Does NOT raise — caller decides whether to block or warn.
        """
        errors: list[str] = []
        p = self._data

        # Geometry
        if p.get("line_length_km", 0) <= 0:
            errors.append("line_length_km must be > 0")
        if p.get("number_of_stations", 0) < 2:
            errors.append("number_of_stations must be ≥ 2 (two terminals minimum)")

        # Speed
        max_speed = p.get("max_speed_kmh", 0)
        design_speed = p.get("design_speed_kmh", 0)
        if max_speed <= 0:
            errors.append("max_speed_kmh must be > 0")
        if design_speed < max_speed:
            errors.append(
                f"design_speed_kmh ({design_speed}) must be ≥ max_speed_kmh ({max_speed})"
            )

        # Headway
        peak_h = p.get("peak_headway_sec", 0)
        offpeak_h = p.get("off_peak_headway_sec", 0)
        if peak_h <= 0:
            errors.append("peak_headway_sec must be > 0")
        if offpeak_h < peak_h:
            errors.append(
                f"off_peak_headway_sec ({offpeak_h}) must be ≥ peak_headway_sec ({peak_h})"
            )

        # Capacity
        seated = p.get("seated_capacity", 0)
        stand4 = p.get("standing_capacity_4ppm2", 0)
        stand6 = p.get("standing_capacity_6ppm2", 0)
        if seated <= 0:
            errors.append("seated_capacity must be > 0")
        if stand4 <= 0:
            errors.append("standing_capacity_4ppm2 must be > 0")
        if stand6 < stand4:
            errors.append(
                f"standing_capacity_6ppm2 ({stand6}) must be ≥ standing_capacity_4ppm2 ({stand4})"
            )

        # RAMS targets
        mtbf = p.get("mtbf_target_hours", 0)
        mttr = p.get("mttr_target_hours", 0)
        if mtbf <= 0:
            errors.append("mtbf_target_hours must be > 0")
        if mttr <= 0:
            errors.append("mttr_target_hours must be > 0")
        if mttr >= mtbf:
            errors.append(
                f"mttr_target_hours ({mttr}) must be < mtbf_target_hours ({mtbf})"
            )

        avail_target = p.get("system_availability_target_pct", 0)
        if not (90.0 <= avail_target < 100.0):
            errors.append(
                f"system_availability_target_pct ({avail_target}) must be in range [90, 100)"
            )

        # Traction
        a  = p.get("max_acceleration_mss", 0)
        d  = p.get("max_deceleration_mss", 0)
        eb = p.get("emergency_deceleration_mss", 0)
        if a <= 0:
            errors.append("max_acceleration_mss must be > 0")
        if d <= 0:
            errors.append("max_deceleration_mss must be > 0")
        if eb < d:
            errors.append(
                f"emergency_deceleration_mss ({eb}) must be ≥ max_deceleration_mss ({d})"
            )

        # Operating hours
        op_hrs = p.get("operating_hours_per_day", 0)
        if not (0 < op_hrs <= 24):
            errors.append(f"operating_hours_per_day ({op_hrs}) must be in (0, 24]")

        # Power
        regen_eff = p.get("regen_recovery_efficiency", -1)
        if not (0 < regen_eff <= 1.0):
            errors.append(f"regen_recovery_efficiency ({regen_eff}) must be in (0, 1]")
        regen_frac = p.get("regen_recoverable_fraction", -1)
        if not (0 < regen_frac <= 1.0):
            errors.append(f"regen_recoverable_fraction ({regen_frac}) must be in (0, 1]")

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self._data, indent=indent, ensure_ascii=False, default=str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectModel":
        return cls(data)

    @classmethod
    def from_json(cls, json_str: str) -> "ProjectModel":
        return cls(json.loads(json_str))

    @classmethod
    def from_file(cls, filepath: Path) -> "ProjectModel":
        with open(filepath, "r", encoding="utf-8") as fh:
            return cls(json.load(fh))

    def save_to_file(self, filepath: Path) -> None:
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(self.to_json())

    # ── Convenience ───────────────────────────────────────────────────────────

    def summary(self) -> dict[str, str]:
        """Human-readable summary for report covers and headers."""
        p = self._data
        return {
            "Project":             p.get("project_name", ""),
            "Country":             p.get("country", ""),
            "Client":              p.get("client", ""),
            "Consultant":          p.get("consultant", ""),
            "Line":                p.get("line_name", ""),
            "Length":              f"{p.get('line_length_km', 0):.1f} km",
            "Stations":            str(p.get("number_of_stations", 0)),
            "Max Speed":           f"{p.get('max_speed_kmh', 0)} km/h",
            "Peak Headway":        f"{p.get('peak_headway_sec', 0)} s",
            "Signalling":          p.get("signalling_system", ""),
            "Power Supply":        p.get("power_supply_voltage", ""),
            "Availability Target": f"{p.get('system_availability_target_pct', 0):.1f}%",
            "GOA Level":           p.get("goa_level", ""),
        }

    def get_station_list(self) -> list[str]:
        stations = self._data.get("station_list", [])
        if not stations:
            n = self._data.get("number_of_stations", 10)
            stations = [f"Station {i+1:02d}" for i in range(n)]
        return stations

    def __repr__(self) -> str:
        return (
            f"ProjectModel(project='{self._data.get('project_name')}', "
            f"line={self._data.get('line_length_km')}km, "
            f"stations={self._data.get('number_of_stations')})"
        )
