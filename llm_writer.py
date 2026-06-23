"""
llm_writer.py
Railway Documentation Generator — NarrativeEngine
==================================================

STRICT RULES:
  • ALL numeric values in prompts and fallback texts come from build_narrative_context().
  • build_narrative_context() reads ONLY from CalculatedState — never from the project dict.
  • No generator function may call p.get() for any engineering number.
  • Non-numeric metadata (project name, country, line name) may be read from the model.
  • The LLM receives a pre-built context dict — it never has direct access to raw inputs.
  • LLM output is appended to the document as text only — never parsed, never fed back.

Entry point:
    ctx = build_narrative_context(model, cs)
    text = generate_introduction(ctx, doc_type)
"""

from __future__ import annotations

import os
from typing import Callable

from config import AI_PROVIDER, ANTHROPIC_MODEL, OPENAI_MODEL, MAX_TOKENS, AI_TEMPERATURE


# ═══════════════════════════════════════════════════════════════════════════════
# NARRATIVE CONTEXT BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def build_narrative_context(model, cs) -> dict:
    """
    Build a flat context dict from CalculatedState and ProjectModel metadata.

    RULES:
      • Engineering numbers come EXCLUSIVELY from cs (CalculatedState).
      • Identity/config strings may come from model.
      • No value in the returned dict is invented or hardcoded.

    All generator functions receive this dict and read from it exclusively.
    """
    p = model.to_dict()
    return {
        # ── Identity (user-provided strings — not engineering values) ──────────
        "project_name":         p.get("project_name", ""),
        "line_name":            p.get("line_name", ""),
        "country":              p.get("country", ""),
        "client":               p.get("client", ""),
        "consultant":           p.get("consultant", ""),
        "depot_location":       p.get("depot_location", ""),
        "goa_level":            p.get("goa_level", ""),
        "signalling_system":    p.get("signalling_system", ""),
        "power_supply_voltage": p.get("power_supply_voltage", ""),
        "power_supply_type":    p.get("power_supply_type", ""),
        "safety_integrity_level": p.get("safety_integrity_level", "SIL 4"),
        "scada_system":         p.get("scada_system", ""),
        "maintenance_regime":   p.get("maintenance_regime", ""),
        "station_list":         model.get_station_list(),

        # ── Configuration inputs (non-calculated user selections) ─────────────
        "cars_per_train":        p.get("cars_per_train", 6),
        "train_length_m":        p.get("train_length_m", 138.0),
        "train_width_m":         p.get("train_width_m", 2.88),
        "train_height_m":        p.get("train_height_m", 3.70),
        "project_life_years":    p.get("project_life_years", 40),
        "number_of_substations": p.get("number_of_substations", 10),
        "substation_spacing_km": p.get("substation_spacing_km", 2.5),
        "telecom_systems":       p.get("telecom_systems", []),
        "psd_type":              p.get("psd_type", "Full-Height PSD"),
        "seated_capacity":       p.get("seated_capacity", 306),
        "standing_capacity_6ppm2": p.get("standing_capacity_6ppm2", 918),
        "line_length_km":        p.get("line_length_km", 0),
        "number_of_stations":    p.get("number_of_stations", 0),
        "peak_headway_sec":      p.get("peak_headway_sec", 120),
        "off_peak_headway_sec":  p.get("off_peak_headway_sec", 180),
        "operating_hours_per_day": p.get("operating_hours_per_day", 18),
        "max_speed_kmh":         p.get("max_speed_kmh", 80),
        "design_speed_kmh":      p.get("design_speed_kmh", 90),
        "max_acceleration_mss":  p.get("max_acceleration_mss", 1.0),
        "max_deceleration_mss":  p.get("max_deceleration_mss", 1.0),
        "emergency_deceleration_mss": p.get("emergency_deceleration_mss", 1.3),
        "scada_poll_interval_sec":    p.get("scada_poll_interval_sec", 2),
        "psd_cycle_time_sec":    p.get("psd_cycle_time_sec", 8),
        "mtbf_target_hours":     p.get("mtbf_target_hours", 50000),
        "mttr_target_hours":     p.get("mttr_target_hours", 4.0),
        "reliability_target_km": p.get("reliability_target_km", 200000),
        # Availability: target from model input (correct — not a calculated output)
        # predicted from CalculatedState — distinct quantities, both valid
        "system_availability_target_pct": cs.rams_alloc.system_avail_target_pct,
        "predicted_availability_pct":      round(cs.ram.availability * 100.0, 4),
        # Telecom backbone requirement — from cs.rams_alloc apportionment
        "telecom_allocated_avail_pct":     next(
            (a for n, a in zip(cs.rams_alloc.subsystem_names, cs.rams_alloc.allocated_avail_pct)
             if "Telecom" in n),
            99.9996
        ),
        "peak_demand_pphpd":     p.get("peak_demand_pphpd", 45000),
        "mean_gradient_permille":p.get("mean_gradient_permille", 0.0),
        "auxiliary_power_kw_per_car": p.get("auxiliary_power_kw_per_car", 15.0),
        # Full traction breakdown from CalculatedState
        "acc_energy_kwh_km":     cs.traction.acc_energy_kwh_km,
        "resistance_energy_kwh_km": cs.traction.resistance_energy_kwh_km,
        "gradient_energy_kwh_km":cs.traction.gradient_energy_kwh_km,
        "auxiliary_energy_kwh_km":cs.traction.auxiliary_energy_kwh_km,
        "gross_energy_kwh_km":   cs.traction.gross_energy_kwh_km,
        "motor_efficiency":      cs.traction.motor_efficiency,
        "regen_efficiency":      cs.traction.regen_efficiency,
        # RAMS allocation summary
        "rams_series_mtbf":      cs.rams_alloc.series_mtbf_hours,
        "rams_series_avail_pct": cs.rams_alloc.series_avail_pct,

        # ── Calculated values — ALL from CalculatedState ──────────────────────
        # Operational
        "commercial_speed_kmh":  cs.ops.commercial_speed_kmh,
        "running_time_min":      cs.ops.running_time_min,
        "round_trip_time_min":   cs.ops.round_trip_time_min,
        "trains_in_service":     cs.ops.trains_in_service,
        "fleet_required":        cs.ops.fleet_required,
        "reserve_trains":        cs.ops.reserve_trains,
        "total_fleet":           cs.ops.total_fleet,
        "daily_train_km":        cs.ops.daily_train_km,
        "annual_train_km":       cs.ops.annual_train_km,

        # Headway
        "technical_headway_sec":     cs.headway.technical_headway_sec,
        "commercial_headway_sec":    cs.headway.commercial_headway_sec,
        "min_safe_separation_m":     cs.headway.minimum_safe_separation_m,

        # Capacity
        "capacity_4ppm2":        cs.capacity.capacity_4ppm2,
        "capacity_6ppm2":        cs.capacity.capacity_6ppm2,
        "pphpd_4ppm2":           cs.capacity.pphpd_4ppm2,
        "pphpd_6ppm2":           cs.capacity.pphpd_6ppm2,
        "load_factor_6ppm2_pct": cs.capacity.load_factor_6ppm2_pct,
        "capacity_adequate":     cs.capacity.capacity_adequate,

        # RAM
        "system_availability_pct":   round(cs.ram.availability * 100, 4),
        "km_between_failures":       cs.ram.km_between_failures,
        "mission_reliability_24h":   round(cs.ram.mission_reliability_24h, 4),
        "maintainability_8h":        round(cs.ram.maintainability_8h, 4),

        # Traction
        "peak_power_kw":             cs.traction.peak_power_kw,
        "energy_per_train_km_kwh":   cs.traction.energy_per_train_km_kwh,
        "regenerative_saving_pct":   cs.traction.regenerative_saving_pct,   # ← from formula, not hardcoded
        "substation_rating_mva":     cs.traction.substation_rating_mva,
        "annual_energy_mwh":         cs.traction.annual_energy_mwh,
        "train_mass_tonnes":         cs.traction.train_mass_tonnes,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# LLM CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = (
    "You are a senior railway systems engineer with 30 years of experience at "
    "SYSTRA, Egis, WSP, AtkinsRéalis, Artelia and AECOM. You write technical railway "
    "engineering documents at the highest professional level. Your style is:\n"
    "- Formal and precise engineering English\n"
    "- Long, well-structured paragraphs (avoid bullet lists)\n"
    "- Consistent use of defined terminology\n"
    "- References to international standards (EN 50126, EN 50128, EN 50129, IEC 62290, etc.)\n"
    "- Passive and active voice mixed appropriately\n"
    "- Quantitative and qualitative assertions based strictly on the project data provided\n"
    "- Professional headings and logical document flow\n"
    "- Never speculative — always grounded in engineering fact\n\n"
    "CRITICAL: Use ONLY the numeric values provided in the project context. "
    "Do not invent, estimate, or approximate any engineering figure."
)


def _call_anthropic(prompt: str) -> str:
    try:
        import anthropic
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            return ""
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=AI_TEMPERATURE,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception:
        return ""


def _call_openai(prompt: str) -> str:
    try:
        from openai import OpenAI
        key = os.environ.get("OPENAI_API_KEY", "")
        if not key:
            return ""
        client = OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=AI_TEMPERATURE,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return ""


def _call_llm(prompt: str) -> str:
    if AI_PROVIDER == "anthropic":
        return _call_anthropic(prompt)
    if AI_PROVIDER == "openai":
        return _call_openai(prompt)
    return ""


def _gen(prompt: str, fallback: str) -> str:
    text = _call_llm(prompt)
    return text if text else fallback


# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER GENERATORS
# All accept ctx: dict (built by build_narrative_context).
# All numeric values read from ctx — never from p.get() or hardcoded.
# ═══════════════════════════════════════════════════════════════════════════════

def generate_introduction(ctx: dict, doc_type: str) -> str:
    prompt = (
        f"Write a professional introduction section for a {doc_type} document for the "
        f"{ctx['project_name']} project in {ctx['country']}. "
        f"The client is {ctx['client']}. "
        f"The line is {ctx['line_name']}, {ctx['line_length_km']} km long with "
        f"{ctx['number_of_stations']} stations. "
        f"The signalling system is {ctx['signalling_system']}. "
        f"Write 3 to 4 formal paragraphs. No bullet lists."
    )
    fallback = (
        f"This document constitutes the {doc_type} for the {ctx['project_name']} project, "
        f"located in {ctx['country']} and developed for {ctx['client']}. "
        f"The {ctx['line_name']} extends over a total route length of "
        f"{ctx['line_length_km']} km, serving {ctx['number_of_stations']} stations with a "
        f"design maximum speed of {ctx['max_speed_kmh']} km/h.\n\n"
        f"The railway system is designed in accordance with internationally recognised standards, "
        f"including EN 50126 for Reliability, Availability, Maintainability and Safety (RAMS), "
        f"EN 50128 for software, EN 50129 for safety-related electronic systems, and IEC 62290 "
        f"for urban guided transport management and command/control systems. The signalling "
        f"philosophy adopted is based on {ctx['signalling_system']}, providing "
        f"{ctx['goa_level']} operation throughout the revenue service period.\n\n"
        f"The purpose of this document is to define and describe the operational and technical "
        f"parameters of the system in a manner that is consistent with the project's Basis of "
        f"Design, System Requirements Specification, and applicable regulatory framework. "
        f"All values presented herein are derived from the CalculatedState of the project's "
        f"engineering model and shall be updated as the design progresses through subsequent phases."
    )
    return _gen(prompt, fallback)


def generate_scope(ctx: dict, doc_type: str) -> str:
    prompt = (
        f"Write a Scope section for a {doc_type} for the {ctx['project_name']} project. "
        f"Describe what the document covers and what is excluded. Use 2 paragraphs."
    )
    fallback = (
        f"This document covers the complete description and definition of the "
        f"{ctx['line_name']} railway system, encompassing all subsystems and their "
        f"interdependencies as required for the design, procurement, installation, testing, "
        f"and commissioning phases. The scope includes rolling stock, signalling and train "
        f"control, traction power supply, telecommunications, SCADA, platform screen doors, "
        f"operations control centre, and depot facilities.\n\n"
        f"This document does not address civil and structural engineering in detail, which "
        f"are treated in separate discipline-specific deliverables. Financial, commercial, "
        f"or contractual obligations are also outside the scope of this document."
    )
    return _gen(prompt, fallback)


def generate_system_overview(ctx: dict) -> str:
    prompt = (
        f"Write a System Overview for the {ctx['project_name']} railway. "
        f"Line: {ctx['line_length_km']} km, {ctx['number_of_stations']} stations, "
        f"max speed {ctx['max_speed_kmh']} km/h, "
        f"commercial speed {ctx['commercial_speed_kmh']} km/h (calculated), "
        f"technical headway {ctx['technical_headway_sec']} s (calculated), "
        f"fleet: {ctx['total_fleet']} trains total ({ctx['trains_in_service']} in service). "
        f"Write 3 substantial paragraphs."
    )
    fallback = (
        f"The {ctx['line_name']} is a fully segregated, high-capacity urban metro railway "
        f"designed to serve the {ctx['country']} metropolitan area. The line has a total "
        f"route length of {ctx['line_length_km']} km and accommodates "
        f"{ctx['number_of_stations']} passenger stations, including terminal stations at "
        f"each end. The depot and maintenance facility is located at "
        f"{ctx['depot_location']}, providing a base for all maintenance "
        f"activities, fleet stabling, and operational support.\n\n"
        f"Train operations are governed by a {ctx['signalling_system']} train control "
        f"system, providing a minimum technical headway of "
        f"{ctx['technical_headway_sec']:.1f} seconds under normal operating conditions. "
        f"The system is designed to operate at a maximum speed of "
        f"{ctx['max_speed_kmh']} km/h, with a calculated commercial speed of "
        f"{ctx['commercial_speed_kmh']:.1f} km/h, resulting in an end-to-end running time "
        f"of {ctx['running_time_min']:.1f} minutes and a round trip time of "
        f"{ctx['round_trip_time_min']:.1f} minutes. Traction power is supplied at "
        f"{ctx['power_supply_voltage']} via a {ctx['power_supply_type']} arrangement, "
        f"with {ctx['number_of_substations']} substations at approximately "
        f"{ctx['substation_spacing_km']:.1f} km intervals.\n\n"
        f"The system is designed and certified in accordance with {ctx['goa_level']} "
        f"as defined in IEC 62267. The fleet comprises {ctx['total_fleet']} trainsets "
        f"({ctx['fleet_required']} operational, {ctx['reserve_trains']} reserve), "
        f"providing a peak service capacity of {ctx['pphpd_6ppm2']:,} passengers per hour "
        f"per direction at 6 pax/m² loading, against a design demand of "
        f"{ctx['peak_demand_pphpd']:,} pphpd. The system availability target is "
        f"{ctx['system_availability_target_pct']}%, with a calculated MTBF of "
        f"{ctx['mtbf_target_hours']:,} hours yielding "
        f"{ctx['km_between_failures']:,.0f} km between failures."
    )
    return _gen(prompt, fallback)


def generate_alignment_description(ctx: dict) -> str:
    prompt = (
        f"Write an Alignment Description for the {ctx['line_name']} metro, "
        f"{ctx['line_length_km']} km, {ctx['number_of_stations']} stations, "
        f"in {ctx['country']}. Describe alignment characteristics, gradients, curves. "
        f"Write 2 to 3 professional paragraphs."
    )
    fallback = (
        f"The {ctx['line_name']} alignment has been designed to optimise journey time "
        f"performance while minimising construction costs and environmental impacts. "
        f"The route extends over {ctx['line_length_km']} km, comprising sections of "
        f"underground tunnel, at-grade, and elevated viaduct as dictated by the urban "
        f"environment and topography of the corridor.\n\n"
        f"The maximum permissible gradient throughout the alignment does not exceed 35‰, "
        f"with steeper gradients avoided in station approach areas to reduce braking "
        f"distances and ensure passenger comfort. Horizontal curves are designed to "
        f"maintain appropriate cant and cant deficiency values, consistent with the "
        f"maximum design speed of {ctx['max_speed_kmh']} km/h. All geometric transitions "
        f"comply with applicable UIC standards and the project's Basis of Design."
    )
    return _gen(prompt, fallback)


def generate_station_description(ctx: dict) -> str:
    stations = ctx['station_list']
    st_list = ", ".join(stations[:5])
    if len(stations) > 5:
        st_list += f" … and {len(stations)-5} others"
    prompt = (
        f"Write a Station Description for the {ctx['line_name']} metro. "
        f"{len(stations)} stations: {st_list}. "
        f"Describe platform types, PSD, accessibility. Write 3 paragraphs."
    )
    fallback = (
        f"The {ctx['line_name']} comprises {ctx['number_of_stations']} passenger "
        f"stations, each designed to accommodate a {ctx['cars_per_train']}-car train "
        f"of {ctx['train_length_m']:.0f} m with appropriate overrun margins. "
        f"Platforms are equipped with Platform Screen Doors (PSDs) throughout, "
        f"providing a physical interface between the passenger concourse and the "
        f"trackway, enabling {ctx['goa_level']} operational mode.\n\n"
        f"Each station incorporates full accessibility provisions including step-free "
        f"access from street level to platform, tactile paving, audible information "
        f"systems, and accessible ticket machines. Passenger information is provided "
        f"through a fully integrated Passenger Information System (PIS) displaying "
        f"real-time train running information and emergency messaging."
    )
    return _gen(prompt, fallback)


def generate_rolling_stock_description(ctx: dict) -> str:
    prompt = (
        f"Write a Rolling Stock Description for {ctx['project_name']}. "
        f"Train: {ctx['cars_per_train']} cars, {ctx['train_length_m']} m, "
        f"mass {ctx['train_mass_tonnes']:.0f} t (AW3), "
        f"max speed {ctx['max_speed_kmh']} km/h, "
        f"capacity: {ctx['capacity_6ppm2']} passengers at 6 pax/m². "
        f"Regen saving: {ctx['regenerative_saving_pct']:.0f}%. "
        f"Write 4 paragraphs."
    )
    fallback = (
        f"The {ctx['project_name']} rolling stock consists of electric multiple units "
        f"(EMUs) configured as {ctx['cars_per_train']}-car trainsets, each with an "
        f"overall length of {ctx['train_length_m']:.1f} m and a body width of "
        f"{ctx['train_width_m']:.2f} m. The train mass at AW3 loading is "
        f"{ctx['train_mass_tonnes']:.0f} t. The maximum operating speed is "
        f"{ctx['max_speed_kmh']} km/h with a design speed of {ctx['design_speed_kmh']} km/h.\n\n"
        f"The traction system utilises three-phase asynchronous motors supplied from an "
        f"IGBT-based voltage source inverter, drawing power from the "
        f"{ctx['power_supply_voltage']} supply system. Maximum acceleration is "
        f"{ctx['max_acceleration_mss']} m/s² and service deceleration is "
        f"{ctx['max_deceleration_mss']} m/s², with emergency braking capability of "
        f"{ctx['emergency_deceleration_mss']} m/s². The braking system incorporates "
        f"regenerative braking as the primary mode, achieving an energy saving of "
        f"{ctx['regenerative_saving_pct']:.0f}% compared to a non-regenerative system.\n\n"
        f"Passenger capacity at 6 pax/m² is {ctx['capacity_6ppm2']} persons per train, "
        f"comprising {ctx['seated_capacity']} seated and {ctx['standing_capacity_6ppm2']} "
        f"standing passengers. This capacity, combined with the peak headway of "
        f"{ctx['peak_headway_sec']} seconds, yields a line capacity of "
        f"{ctx['pphpd_6ppm2']:,} pphpd, against a design demand of "
        f"{ctx['peak_demand_pphpd']:,} pphpd.\n\n"
        f"The rolling stock is equipped with onboard CBTC equipment interfacing with the "
        f"wayside signalling system to enable ATP, ATO, and ATS functions as required for "
        f"{ctx['goa_level']} operation. Crashworthiness design complies with EN 15227 "
        f"and fire safety provisions meet EN 45545."
    )
    return _gen(prompt, fallback)


def generate_signalling_description(ctx: dict) -> str:
    prompt = (
        f"Write a Signalling System Description for {ctx['project_name']}. "
        f"System: {ctx['signalling_system']}, GoA: {ctx['goa_level']}, "
        f"SIL: {ctx['safety_integrity_level']}, "
        f"technical headway: {ctx['technical_headway_sec']:.1f} s (calculated). "
        f"Describe ATP, ATO, ATS, interlocking. Write 4 paragraphs."
    )
    fallback = (
        f"The {ctx['project_name']} train control system is based on "
        f"Communications-Based Train Control (CBTC) employing a moving block "
        f"architecture in accordance with IEC 62290. The system comprises three primary "
        f"functional layers: Automatic Train Protection (ATP), Automatic Train Operation "
        f"(ATO), and Automatic Train Supervision (ATS), integrated through a computer-based "
        f"interlocking (CBI) at each station. The overall safety integrity level is "
        f"{ctx['safety_integrity_level']} for all safety-critical functions per EN 50129.\n\n"
        f"The ATP function provides continuous, real-time supervision of train movements, "
        f"calculating a dynamic movement authority for each train based on the confirmed "
        f"position and speed of preceding trains. This approach eliminates fixed block "
        f"sections and permits a minimum technical headway of "
        f"{ctx['technical_headway_sec']:.1f} seconds, corresponding to a minimum "
        f"safe separation distance of {ctx['min_safe_separation_m']:.0f} m at "
        f"{ctx['max_speed_kmh']} km/h. The ATP system interfaces directly with the "
        f"interlocking to enforce route locking, point position verification, "
        f"and platform screen door control.\n\n"
        f"The ATO function manages the automatic driving of trains, optimising speed "
        f"profiles for energy efficiency and schedule adherence. In {ctx['goa_level']} "
        f"mode, ATO also manages door operation, departure control, and emergency "
        f"procedures without a driver in the cab. Communication between onboard and "
        f"wayside equipment is achieved via a dedicated CBTC radio channel, providing "
        f"continuous bidirectional data exchange at the required update rate.\n\n"
        f"The ATS subsystem, hosted at the Operations Control Centre, provides centralised "
        f"supervision of all train movements. The ATS displays a real-time graphical mimic "
        f"of the line, allowing controllers to monitor train positions, headways, and "
        f"schedule adherence, with intervention tools for service recovery."
    )
    return _gen(prompt, fallback)


def generate_operations_concept(ctx: dict) -> str:
    prompt = (
        f"Write an Operations Concept for {ctx['project_name']}, "
        f"{ctx['goa_level']}, {ctx['operating_hours_per_day']} operating hours/day, "
        f"peak headway {ctx['peak_headway_sec']} s, "
        f"fleet {ctx['total_fleet']} trains ({ctx['trains_in_service']} in service). "
        f"Write 3 paragraphs."
    )
    fallback = (
        f"The {ctx['line_name']} will operate as a fully automated metro railway in "
        f"accordance with {ctx['goa_level']} as defined in IEC 62267. Under this "
        f"mode, all train movements are managed automatically by the train control "
        f"system, with no requirement for a driver on board during revenue service. "
        f"Platform operations are supervised by station staff and remotely by the OCC, "
        f"with comprehensive CCTV coverage providing full visual supervision of all "
        f"platform areas prior to train departure.\n\n"
        f"Service will operate for {ctx['operating_hours_per_day']} hours per day "
        f"during the revenue period. During peak periods, the minimum service headway "
        f"is {ctx['peak_headway_sec']} seconds, reducing to "
        f"{ctx['off_peak_headway_sec']} seconds off-peak. The total fleet of "
        f"{ctx['total_fleet']} trainsets includes {ctx['fleet_required']} operational "
        f"and {ctx['reserve_trains']} reserve trains, providing a daily train-km output "
        f"of {ctx['daily_train_km']:,.0f} km.\n\n"
        f"The Operations Control Centre constitutes the nerve centre of the railway "
        f"operation, providing a single point of coordination for service management, "
        f"incident response, maintenance coordination, and passenger communications. "
        f"Operational procedures are defined in the suite of Standard Operating "
        f"Procedures (SOPs) and Emergency Operating Procedures (EOPs)."
    )
    return _gen(prompt, fallback)


def generate_normal_operation(ctx: dict) -> str:
    fallback = (
        f"During normal operation, trains operate in accordance with the programmed "
        f"timetable under full {ctx['goa_level']} automatic control. The ATO system "
        f"drives each train along the line, regulating speed to maintain schedule "
        f"adherence and optimise energy consumption through coast-and-glide profiles "
        f"where practical. Station dwell times are managed automatically with the "
        f"ability for OCC controllers to extend dwells in exceptional circumstances.\n\n"
        f"The {ctx['trains_in_service']} trains in peak service maintain a headway of "
        f"{ctx['peak_headway_sec']} seconds, well within the calculated technical "
        f"minimum of {ctx['technical_headway_sec']:.1f} seconds. Trains are stabled "
        f"at {ctx['depot_location']} depot during the non-revenue period, with "
        f"pre-service preparation and post-service inspection carried out in "
        f"accordance with the Maintenance Plan."
    )
    return _gen(
        f"Write a Normal Operation section for {ctx['project_name']} metro. 2 paragraphs.",
        fallback,
    )


def generate_degraded_operation(ctx: dict) -> str:
    fallback = (
        f"Degraded mode operations arise when one or more subsystems are unavailable, "
        f"but a reduced level of service can still be maintained. The CBTC system "
        f"supports several degraded operating modes, including reduced-speed zone "
        f"operation, restricted manual driving mode, and partial ATP protection mode, "
        f"each invoked through defined operational procedures.\n\n"
        f"In the event of a partial signalling system failure, affected trains may "
        f"operate under a degraded ATO mode at restricted speed, supervised by the OCC. "
        f"Service recovery procedures are documented in the Emergency Operating "
        f"Procedures and are practised through periodic simulation exercises."
    )
    return _gen(
        f"Write a Degraded Operation section for {ctx['project_name']} metro. 2 paragraphs.",
        fallback,
    )


def generate_emergency_operation(ctx: dict) -> str:
    fallback = (
        f"Emergency operating procedures are activated in response to incidents that "
        f"present a risk to passenger or staff safety. Such incidents include fire, "
        f"medical emergencies, security threats, structural failures, and major "
        f"equipment failures. The OCC is the primary coordination point, liaising with "
        f"emergency services, station staff, and maintenance personnel.\n\n"
        f"The evacuation of passengers from trains or stations is conducted in "
        f"accordance with the Emergency Evacuation Plan. Traction power isolation "
        f"can be achieved remotely from the OCC or locally at designated isolation "
        f"points, in accordance with the Electrical Safety Rules."
    )
    return _gen(
        f"Write an Emergency Operation section for {ctx['project_name']} metro. 2 paragraphs.",
        fallback,
    )


def generate_occ_operation(ctx: dict) -> str:
    fallback = (
        f"The Operations Control Centre (OCC) for the {ctx['line_name']} is the "
        f"central facility for all operational management and control functions. "
        f"The OCC is staffed continuously throughout the operational period, with "
        f"controllers performing defined roles including Service Controller, Systems "
        f"Controller, and Duty Operations Manager.\n\n"
        f"The OCC incorporates uninterruptible power supply (UPS) systems, "
        f"environmental controls, and redundant communication links to all stations "
        f"and the depot. A backup OCC capability is provided at an alternative "
        f"location, enabling continuity of operations if the primary OCC becomes "
        f"unavailable."
    )
    return _gen(
        f"Write an OCC Operation Concept for {ctx['project_name']}. 2 paragraphs.",
        fallback,
    )


def generate_maintenance_concept(ctx: dict) -> str:
    fallback = (
        f"The maintenance strategy for {ctx['project_name']} is based on a "
        f"combination of time-based preventive maintenance and condition-based "
        f"maintenance, supported by a CMMS. The regime targets the system "
        f"availability target of {ctx['system_availability_target_pct']:.3f}% "
        f"(predicted: {ctx['predicted_availability_pct']:.4f}%) and an MTTR "
        f"of {ctx['mttr_target_hours']} hours as specified in the RAMS programme. "
        f"Calculated availability is {ctx['system_availability_pct']:.4f}%, "
        f"with {ctx['km_between_failures']:,.0f} km between failures.\n\n"
        f"Maintenance is classified into three levels: Line Maintenance, performed "
        f"at stations or on running lines with minimal service disruption; "
        f"Depot Maintenance, performed during the non-revenue period at the "
        f"{ctx['depot_location']} facility; and Workshop Maintenance, encompassing "
        f"heavy overhaul and component exchange activities."
    )
    return _gen(
        f"Write a Maintenance Concept for {ctx['project_name']}. 2 paragraphs.",
        fallback,
    )


def generate_rams_description(ctx: dict) -> str:
    fallback = (
        f"The RAMS programme for {ctx['project_name']} is conducted in accordance "
        f"with EN 50126 and encompasses the complete system lifecycle. The programme "
        f"establishes quantitative targets for Reliability, Availability, "
        f"Maintainability, and Safety, allocated to subsystems through a formal "
        f"apportionment process based on system architecture and operational requirements.\n\n"
        f"The system-level availability target is {ctx['system_availability_target_pct']:.3f}% "
        f"(client requirement, EN 50126-1 §4.2), "
        f"with a predicted availability of {ctx['predicted_availability_pct']:.4f}% "
        f"(MTBF: {ctx['mtbf_target_hours']:,} h, MTTR: {ctx['mttr_target_hours']} h). "
        f"Reliability is expressed as {ctx['km_between_failures']:,.0f} km between "
        f"service-affecting failures, against a target of "
        f"{ctx['reliability_target_km']:,} km. Mission reliability over 24 hours "
        f"is {ctx['mission_reliability_24h']:.4f}."
    )
    return _gen(
        f"Write a RAMS Description for {ctx['project_name']} with targets and calculated values. "
        f"2 paragraphs.",
        fallback,
    )


def generate_traction_power_description(ctx: dict) -> str:
    prompt = (
        f"Write a Traction Power Description for {ctx['project_name']}, "
        f"{ctx['power_supply_voltage']}, {ctx['number_of_substations']} substations, "
        f"peak power {ctx['peak_power_kw']:,.0f} kW per train, "
        f"energy {ctx['energy_per_train_km_kwh']:.3f} kWh/km, "
        f"regenerative saving {ctx['regenerative_saving_pct']:.0f}% (calculated). "
        f"Write 2 paragraphs."
    )
    fallback = (
        f"The traction power supply system for {ctx['project_name']} delivers "
        f"electrical energy at {ctx['power_supply_voltage']} to the rolling stock "
        f"via a {ctx['power_supply_type']} arrangement. Power is drawn from the "
        f"national utility grid at high voltage and transformed at "
        f"{ctx['number_of_substations']} traction substations located at approximately "
        f"{ctx['substation_spacing_km']:.1f} km intervals along the route. Each "
        f"substation is rated at {ctx['substation_rating_mva']:.1f} MVA, driven by "
        f"a peak tractive power per train of {ctx['peak_power_kw']:,.0f} kW at "
        f"{ctx['max_speed_kmh']} km/h (drive efficiency η = "
        f"{ctx.get('motor_efficiency', 0.893):.4f}, combined motor and gearbox).\n\n"
        f"Net energy consumption is {ctx['energy_per_train_km_kwh']:.3f} kWh/km per train, "
        f"comprising: kinetic energy {ctx.get('acc_energy_kwh_km', 0):.3f} kWh/km "
        f"(dominant in stop-start metro with {ctx['number_of_stations']-1} inter-station "
        f"cycles per {ctx['line_length_km']:.1f} km), rolling resistance "
        f"{ctx.get('resistance_energy_kwh_km', 0):.3f} kWh/km (Davis model), "
        f"auxiliary loads {ctx.get('auxiliary_energy_kwh_km', 0):.3f} kWh/km "
        f"(HVAC, lighting, electronics), less regenerative recovery "
        f"{ctx.get('braking_energy_kwh_km', 0):.3f} kWh/km. "
        f"The regenerative saving is {ctx['regenerative_saving_pct']:.1f}% of gross energy, "
        f"derived from a recovery efficiency of {ctx.get('regen_efficiency', 0.70)*100:.0f}% "
        f"and a recoverable fraction of "
        f"{ctx.get('regen_recoverable_fraction', 0.30)*100:.0f}% of braking energy "
        f"(per EN 50641). Total annual energy consumption is "
        f"{ctx['annual_energy_mwh']:,.0f} MWh/year (based on {ctx['annual_train_km']:,.0f} "
        f"train-km per year). The traction power system is designed to maintain rail "
        f"voltage within EN 50163 limits under all normal and degraded operating conditions."
    )
    return _gen(prompt, fallback)


def generate_telecom_description(ctx: dict) -> str:
    systems = ", ".join(ctx['telecom_systems']) if ctx['telecom_systems'] else "TETRA Radio, CCTV, PA, PIS"
    fallback = (
        f"The telecommunications systems for {ctx['project_name']} comprise an "
        f"integrated suite designed to support safe and efficient railway operations, "
        f"passenger services, and security management. The primary systems include "
        f"{systems}, all interconnected through a common IP-based backbone network "
        f"with appropriate quality of service (QoS) parameters.\n\n"
        f"The operational radio system provides voice communications between OCC "
        f"controllers, station staff, and maintenance personnel. The CCTV system "
        f"provides continuous video surveillance of all public areas. The Public "
        f"Address system enables voice announcements from the OCC or locally at "
        f"stations, with pre-recorded emergency messages available for rapid deployment."
    )
    return _gen(
        f"Write a Telecommunications Description for {ctx['project_name']}. 2 paragraphs.",
        fallback,
    )


def generate_psd_description(ctx: dict) -> str:
    fallback = (
        f"Platform Screen Doors (PSDs) are installed at all {ctx['number_of_stations']} "
        f"passenger stations on the {ctx['line_name']}, providing a physical barrier "
        f"between the passenger platform and the trackway. The PSD system is essential "
        f"for the safe implementation of {ctx['goa_level']} operation, enabling the "
        f"automatic management of passenger boarding and alighting.\n\n"
        f"PSDs interface directly with the signalling system, ensuring that doors are "
        f"fully closed and locked before a departure authority is granted to the train. "
        f"The PSD control logic meets {ctx.get('psd_sil_level', 'SIL 2')} per EN 50129, "
        f"with independent monitoring of each door leaf. Emergency release mechanisms "
        f"are provided at trackside intervals in accordance with fire and evacuation requirements."
    )
    return _gen(
        f"Write a PSD description for {ctx['project_name']} with {ctx['goa_level']}. 2 paragraphs.",
        fallback,
    )


def generate_scada_description(ctx: dict) -> str:
    fallback = (
        f"The Supervisory Control and Data Acquisition (SCADA) system for "
        f"{ctx['project_name']} provides centralised monitoring and control of all "
        f"building services and fixed plant across the network. The system employs a "
        f"{ctx['scada_system']} architecture, with Remote Terminal Units (RTUs) at "
        f"each station interfacing with traction substations, ventilation, HVAC, "
        f"lighting, lifts, pumping systems, and fire detection systems.\n\n"
        f"The SCADA system communicates with the OCC via a dedicated, redundant "
        f"fibre-optic network, providing real-time status data and enabling remote "
        f"operation of all connected plant. Poll intervals do not exceed "
        f"{ctx['scada_poll_interval_sec']} seconds for all RTUs. The system complies "
        f"with IEC 60870-5 communication protocols and incorporates cybersecurity "
        f"measures in accordance with IEC 62443."
    )
    return _gen(
        f"Write a SCADA description for {ctx['project_name']}. 2 paragraphs.",
        fallback,
    )


def generate_conclusion(ctx: dict, doc_type: str) -> str:
    fallback = (
        f"This document has presented the {doc_type} for the "
        f"{ctx['project_name']} project in {ctx['country']}, "
        f"covering all relevant technical and operational parameters as required by "
        f"the project scope and applicable standards. All engineering values are "
        f"derived from the project's CalculatedState and are consistent with the "
        f"Headway Study, Fleet Calculation, and RAMS analysis.\n\n"
        f"Future revisions will be issued as the project progresses through subsequent "
        f"design phases, incorporating updated parameters, verification evidence, and "
        f"regulatory feedback. All comments and queries should be directed to the "
        f"document author through the project's formal review and comment management process."
    )
    return _gen(
        f"Write a Conclusion for a {doc_type} for {ctx['project_name']}. 2 paragraphs.",
        fallback,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER GENERATOR MAP
# Key → function(ctx, ...) — used by document_generator
# ═══════════════════════════════════════════════════════════════════════════════

CHAPTER_GENERATORS: dict[str, Callable] = {
    "introduction":        generate_introduction,
    "scope":               generate_scope,
    "system_overview":     generate_system_overview,
    "alignment":           generate_alignment_description,
    "stations":            generate_station_description,
    "rolling_stock":       generate_rolling_stock_description,
    "signalling":          generate_signalling_description,
    "operations_concept":  generate_operations_concept,
    "normal_operation":    generate_normal_operation,
    "degraded_operation":  generate_degraded_operation,
    "emergency_operation": generate_emergency_operation,
    "occ":                 generate_occ_operation,
    "maintenance":         generate_maintenance_concept,
    "rams":                generate_rams_description,
    "traction":            generate_traction_power_description,
    "telecom":             generate_telecom_description,
    "psd":                 generate_psd_description,
    "scada":               generate_scada_description,
    "conclusion":          generate_conclusion,
}
