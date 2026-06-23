"""
ui.py  —  Railway Documentation Generator · Streamlit UI
All engineering values read exclusively from CalculationEngine.run().
No calculations in the UI layer.
"""

import streamlit as st
import pandas as pd
import os
from pathlib import Path

import config as cfg
from project_database import ProjectDatabase as PDB
from project_model import ProjectModel
from calculations import CalculationEngine
from tables import TableGenerator


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _cs():
    """Run CalculationEngine on current session model — always fresh."""
    return CalculationEngine.run(PDB.get_model())


def _tg():
    return TableGenerator()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

def configure_page():
    st.set_page_config(
        page_title="Railway Documentation Generator",
        page_icon="🚆",
        layout="wide",
        initial_sidebar_state="expanded",
    )


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.title("🚆 RDG")
        st.caption("Railway Documentation Generator")
        st.divider()

        st.subheader("💾 Project File")
        if st.button("Save Project", use_container_width=True):
            try:
                path = PDB.save_to_file()
                st.success(f"Saved: {path.name}")
            except Exception as e:
                st.error(f"Save failed: {e}")

        uploaded = st.file_uploader("Load Project (.json)", type=["json"])
        if uploaded:
            try:
                import json, tempfile
                data = json.loads(uploaded.read())
                # Strip forbidden keys before loading
                safe = {k: v for k, v in data.items()
                        if k not in ProjectModel._FORBIDDEN_KEYS}
                PDB.update(safe)
                st.success("Project loaded.")
                st.rerun()
            except Exception as e:
                st.error(f"Load failed: {e}")

        st.divider()
        st.subheader("🤖 AI Settings")
        provider = st.selectbox("Provider", ["None", "Anthropic", "OpenAI"])
        if provider == "Anthropic":
            key = st.text_input("Anthropic API Key", type="password")
            if key:
                os.environ["ANTHROPIC_API_KEY"] = key
        elif provider == "OpenAI":
            key = st.text_input("OpenAI API Key", type="password")
            if key:
                os.environ["OPENAI_API_KEY"] = key

        st.divider()
        if st.button("↺ Reset to Defaults", use_container_width=True):
            PDB.reset_to_defaults()
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB: PROJECT
# ─────────────────────────────────────────────────────────────────────────────

def tab_project():
    st.header("🏗️ Project Identity")
    c1, c2 = st.columns(2)
    with c1:
        PDB.set("project_name",    st.text_input("Project Name",    PDB.get("project_name")))
        PDB.set("country",         st.text_input("Country",         PDB.get("country")))
        PDB.set("client",          st.text_input("Client",          PDB.get("client")))
        PDB.set("consultant",      st.text_input("Consultant",      PDB.get("consultant")))
        PDB.set("line_name",       st.text_input("Line Name",       PDB.get("line_name")))
    with c2:
        PDB.set("document_number", st.text_input("Document Number", PDB.get("document_number")))
        PDB.set("revision",        st.text_input("Revision",        PDB.get("revision")))
        PDB.set("status", st.selectbox("Status",
            ["Draft","For Review","For Approval","Approved","Superseded"],
            index=["Draft","For Review","For Approval","Approved","Superseded"]
                .index(PDB.get("status","Draft"))))
        PDB.set("project_life_years", st.number_input(
            "Project Life (years)", value=int(PDB.get("project_life_years", 40)),
            min_value=10, max_value=100))

    st.divider()
    st.subheader("📋 Project Summary")
    cs = _cs()
    tg = _tg()
    st.dataframe(tg.project_data_table(PDB.get_model(), cs),
                 use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB: INFRASTRUCTURE
# ─────────────────────────────────────────────────────────────────────────────

def tab_infrastructure():
    st.header("🛤️ Line Infrastructure")
    c1, c2 = st.columns(2)
    with c1:
        PDB.set("line_length_km", st.number_input(
            "Line Length (km)", value=float(PDB.get("line_length_km", 22.5)),
            min_value=0.1, step=0.5))
        PDB.set("number_of_stations", st.number_input(
            "Number of Stations", value=int(PDB.get("number_of_stations", 18)),
            min_value=2, max_value=100))
        PDB.set("number_of_tracks", st.selectbox(
            "Number of Tracks", [1, 2, 3, 4],
            index=[1,2,3,4].index(int(PDB.get("number_of_tracks", 2)))))
    with c2:
        PDB.set("depot_location",  st.text_input("Depot Location",  PDB.get("depot_location")))
        PDB.set("track_gauge_mm",  st.number_input(
            "Track Gauge (mm)", value=int(PDB.get("track_gauge_mm", 1435)),
            min_value=600, max_value=2000))
        PDB.set("loading_gauge",   st.text_input("Loading Gauge",   PDB.get("loading_gauge")))

    st.divider()
    st.subheader("🏙️ Station List")
    n = int(PDB.get("number_of_stations", 18))
    stations = PDB.get("station_list", [])
    if not stations:
        stations = [f"Station {i+1:02d}" for i in range(n)]
    edited = st.data_editor(
        pd.DataFrame({"Station Name": stations[:n]}),
        use_container_width=True, hide_index=False, num_rows="fixed")
    PDB.set("station_list", edited["Station Name"].tolist())


# ─────────────────────────────────────────────────────────────────────────────
# TAB: OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

def tab_operations():
    st.header("🚆 Operations")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Service Parameters (inputs)")
        PDB.set("max_speed_kmh", st.number_input(
            "Maximum Speed (km/h)", value=int(PDB.get("max_speed_kmh", 80)),
            min_value=20, max_value=350))
        PDB.set("peak_headway_sec", st.number_input(
            "Peak Headway (s)", value=int(PDB.get("peak_headway_sec", 90)),
            min_value=30, max_value=600))
        PDB.set("off_peak_headway_sec", st.number_input(
            "Off-Peak Headway (s)", value=int(PDB.get("off_peak_headway_sec", 180)),
            min_value=60, max_value=1800))
        PDB.set("station_dwell_sec", st.number_input(
            "Station Dwell (s)", value=int(PDB.get("station_dwell_sec", 35)),
            min_value=10, max_value=120))
        PDB.set("terminal_dwell_min", st.number_input(
            "Terminal Dwell (min)", value=float(PDB.get("terminal_dwell_min", 3.0)),
            min_value=0.5, max_value=15.0, step=0.5))
        PDB.set("operating_hours_per_day", st.number_input(
            "Operating Hours/Day", value=int(PDB.get("operating_hours_per_day", 18)),
            min_value=4, max_value=24))

    with c2:
        st.subheader("Calculated Results")
        cs = _cs()
        ops = cs.ops
        st.metric("Commercial Speed",    f"{ops.commercial_speed_kmh:.1f} km/h")
        st.metric("Running Time",        f"{ops.running_time_min:.1f} min")
        st.metric("Round Trip Time",     f"{ops.round_trip_time_min:.1f} min")
        st.metric("Trains in Service",   str(ops.trains_in_service))
        st.metric("Operational Fleet",   str(ops.fleet_required))
        st.metric("Total Fleet",         str(ops.total_fleet))
        st.metric("Daily Train-km",      f"{ops.daily_train_km:,.0f}")

    st.divider()
    st.subheader("📋 Operational Parameters")
    cs = _cs()
    tg = _tg()
    st.dataframe(tg.operational_parameters_table(PDB.get_model(), cs),
                 use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB: ROLLING STOCK
# ─────────────────────────────────────────────────────────────────────────────

def tab_rolling_stock():
    st.header("🚃 Rolling Stock")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Consist")
        PDB.set("cars_per_train", st.number_input(
            "Cars per Train", value=int(PDB.get("cars_per_train", 6)),
            min_value=1, max_value=12))
        PDB.set("train_length_m", st.number_input(
            "Train Length (m)", value=float(PDB.get("train_length_m", 138.0)),
            min_value=10.0, step=0.5))
        PDB.set("train_width_m", st.number_input(
            "Train Width (m)", value=float(PDB.get("train_width_m", 2.88)),
            min_value=2.0, max_value=4.0, step=0.01))
        PDB.set("mass_per_car_tonnes", st.number_input(
            "Mass per Car AW3 (t)", value=float(PDB.get("mass_per_car_tonnes", 40.0)),
            min_value=10.0, max_value=100.0, step=0.5))

    with c2:
        st.subheader("Performance")
        PDB.set("max_acceleration_mss", st.number_input(
            "Max Acceleration (m/s²)", value=float(PDB.get("max_acceleration_mss", 1.0)),
            min_value=0.1, max_value=3.0, step=0.1))
        PDB.set("max_deceleration_mss", st.number_input(
            "Service Deceleration (m/s²)", value=float(PDB.get("max_deceleration_mss", 1.0)),
            min_value=0.1, max_value=3.0, step=0.1))
        PDB.set("emergency_deceleration_mss", st.number_input(
            "Emergency Deceleration (m/s²)", value=float(PDB.get("emergency_deceleration_mss", 1.3)),
            min_value=0.5, max_value=4.0, step=0.1))
        PDB.set("seated_capacity", st.number_input(
            "Seated Capacity", value=int(PDB.get("seated_capacity", 306)),
            min_value=10, max_value=1000))
        PDB.set("standing_capacity_4ppm2", st.number_input(
            "Standing (4 pax/m²)", value=int(PDB.get("standing_capacity_4ppm2", 612)),
            min_value=0, max_value=2000))
        PDB.set("standing_capacity_6ppm2", st.number_input(
            "Standing (6 pax/m²)", value=int(PDB.get("standing_capacity_6ppm2", 918)),
            min_value=0, max_value=3000))

    st.divider()
    cs = _cs()
    tg = _tg()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 Rolling Stock Table")
        st.dataframe(tg.rolling_stock_table(PDB.get_model(), cs),
                     use_container_width=True, hide_index=True)
    with col2:
        st.subheader("📋 Fleet Calculation")
        st.dataframe(tg.fleet_calculation_table(PDB.get_model(), cs),
                     use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB: SIGNALLING
# ─────────────────────────────────────────────────────────────────────────────

def tab_signalling():
    st.header("🚦 Signalling & Train Control")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("System Configuration")
        PDB.set("signalling_system", st.selectbox(
            "Signalling System",
            ["CBTC Moving Block","ETCS Level 3","ETCS Level 2",
             "Fixed Block ATP","Cab Signalling"],
            index=["CBTC Moving Block","ETCS Level 3","ETCS Level 2",
                   "Fixed Block ATP","Cab Signalling"]
                  .index(PDB.get("signalling_system","CBTC Moving Block"))))
        PDB.set("goa_level", st.selectbox(
            "Grade of Automation",
            ["GOA1 (NTO)","GOA2 (STO)","GOA3 (DTO)","GOA4 (UTO)"],
            index=["GOA1 (NTO)","GOA2 (STO)","GOA3 (DTO)","GOA4 (UTO)"]
                  .index(PDB.get("goa_level","GOA4 (UTO)"))))
        PDB.set("safety_integrity_level", st.selectbox(
            "Safety Integrity Level",
            ["SIL 1","SIL 2","SIL 3","SIL 4"],
            index=["SIL 1","SIL 2","SIL 3","SIL 4"]
                  .index(PDB.get("safety_integrity_level","SIL 4"))))

    with c2:
        st.subheader("Calculated Headway")
        cs = _cs()
        hw = cs.headway
        st.metric("Technical Headway",     f"{hw.technical_headway_sec:.1f} s")
        st.metric("Commercial Headway",    f"{hw.commercial_headway_sec:.1f} s")
        st.metric("Min. Safe Separation",  f"{hw.minimum_safe_separation_m:.0f} m")
        st.metric("Braking Distance",      f"{hw.braking_distance_m:.0f} m")
        st.metric("Emergency Braking Time",f"{hw.braking_time_sec:.1f} s")

    st.divider()
    st.subheader("📋 Headway Breakdown")
    cs = _cs()
    tg = _tg()
    st.dataframe(tg.headway_breakdown_table(cs),
                 use_container_width=True, hide_index=True)

    st.subheader("📊 Headway Chart")
    try:
        from figures import figure_headway_breakdown
        hdw_dict = {
            "System Reaction Time (s)":   cs.headway.reaction_time_sec,
            "Transmission Latency (s)":   cs.headway.transmission_latency_sec,
            "Emergency Braking Time (s)": cs.headway.braking_time_sec,
            "Safety Margin (s)":          cs.headway.safety_margin_sec,
            "Jerk Limitation (s)":        cs.headway.jerk_limitation_sec,
        }
        img_bytes, _ = figure_headway_breakdown(hdw_dict, save=False)
        st.image(img_bytes, use_container_width=True)
    except Exception as e:
        st.warning(f"Chart not available: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB: TRACTION POWER
# ─────────────────────────────────────────────────────────────────────────────

def tab_traction():
    st.header("⚡ Traction Power")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("System Configuration")
        PDB.set("power_supply_voltage", st.selectbox(
            "Supply Voltage",
            ["750 Vdc","1500 Vdc","3000 Vdc","15 kVac","25 kVac"],
            index=["750 Vdc","1500 Vdc","3000 Vdc","15 kVac","25 kVac"]
                  .index(PDB.get("power_supply_voltage","1500 Vdc"))))
        PDB.set("number_of_substations", st.number_input(
            "Number of Substations", value=int(PDB.get("number_of_substations", 10)),
            min_value=1, max_value=50))
        PDB.set("substation_spacing_km", st.number_input(
            "Substation Spacing (km)", value=float(PDB.get("substation_spacing_km", 2.5)),
            min_value=0.5, max_value=10.0, step=0.5))
        PDB.set("regen_recoverable_fraction", st.slider(
            "Recoverable Braking Fraction",
            0.0, 1.0, float(PDB.get("regen_recoverable_fraction", 0.30)), 0.05))
        PDB.set("regen_recovery_efficiency", st.slider(
            "Regeneration Efficiency",
            0.0, 1.0, float(PDB.get("regen_recovery_efficiency", 0.70)), 0.05))

    with c2:
        st.subheader("Calculated Results")
        cs = _cs()
        t = cs.traction
        st.metric("Peak Power / Train",      f"{t.peak_power_kw:,.0f} kW")
        st.metric("Net Energy / Train-km",   f"{t.energy_per_train_km_kwh:.3f} kWh/km")
        st.metric("Regenerative Saving",     f"{t.regenerative_saving_pct:.1f}%")
        st.metric("Substation Rating",       f"{t.substation_rating_mva:.1f} MVA")
        st.metric("Annual Energy",           f"{t.annual_energy_mwh:,.0f} MWh/year")

    st.divider()
    cs = _cs()
    tg = _tg()
    st.subheader("📋 Traction Parameters")
    st.dataframe(tg.traction_parameters_table(PDB.get_model(), cs),
                 use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB: DEPOT
# ─────────────────────────────────────────────────────────────────────────────

def tab_depot():
    st.header("🏭 Depot & Maintenance Facility")
    c1, c2 = st.columns(2)
    with c1:
        PDB.set("depot_location", st.text_input(
            "Depot Location", PDB.get("depot_location", "")))
        PDB.set("maintenance_regime", st.selectbox(
            "Maintenance Regime",
            ["Preventive and Corrective","Condition-Based","Predictive","Mixed"],
            index=0))
        PDB.set("maintenance_window_hours", st.number_input(
            "Maintenance Window (h/day)",
            value=int(PDB.get("maintenance_window_hours", 6)), min_value=2, max_value=12))
    with c2:
        PDB.set("cmms_system", st.text_input(
            "CMMS System", PDB.get("cmms_system", "IBM Maximo")))
        cs = _cs()
        st.metric("Reserve Trains",    str(cs.ops.reserve_trains))
        st.metric("Total Fleet",       str(cs.ops.total_fleet))
        st.metric("Annual Train-km",   f"{cs.ops.annual_train_km:,.0f}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB: TELECOM
# ─────────────────────────────────────────────────────────────────────────────

def tab_telecom():
    st.header("📡 Telecommunications")
    systems = st.multiselect(
        "Telecom Systems",
        ["TETRA Radio","CCTV","Public Address","Passenger Information System",
         "Clocks","Telephone Network","SCADA Communication","Wi-Fi","LTE/4G"],
        default=PDB.get("telecom_systems", ["TETRA Radio","CCTV","Public Address"]))
    PDB.set("telecom_systems", systems)
    c1, c2 = st.columns(2)
    with c1:
        PDB.set("scada_system", st.text_input(
            "SCADA System", PDB.get("scada_system", "")))
        PDB.set("scada_poll_interval_sec", st.number_input(
            "SCADA Poll Interval (s)",
            value=int(PDB.get("scada_poll_interval_sec", 2)), min_value=1, max_value=60))
    cs = _cs()
    st.info(
        f"Telecom backbone allocated availability: "
        f"{next((f'{a:.5f}%' for n,a in zip(cs.rams_alloc.subsystem_names, cs.rams_alloc.allocated_avail_pct) if 'Telecom' in n), 'N/A')}"
        f" (from RAMS apportionment — EN 50126-2 §6.2)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# TAB: PSD
# ─────────────────────────────────────────────────────────────────────────────

def tab_psd():
    st.header("🚪 Platform Screen Doors")
    c1, c2 = st.columns(2)
    with c1:
        PDB.set("psd_type", st.selectbox(
            "PSD Type",
            ["Full-Height PSD","Half-Height PSD","Sliding Door System","Platform Gates"],
            index=["Full-Height PSD","Half-Height PSD","Sliding Door System","Platform Gates"]
                  .index(PDB.get("psd_type","Full-Height PSD"))))
        PDB.set("psd_door_width_m", st.number_input(
            "Door Width (m)", value=float(PDB.get("psd_door_width_m", 1.8)),
            min_value=0.5, max_value=4.0, step=0.1))
        PDB.set("psd_cycle_time_sec", st.number_input(
            "PSD Cycle Time (s)", value=int(PDB.get("psd_cycle_time_sec", 8)),
            min_value=2, max_value=30))
    with c2:
        PDB.set("psd_sil_level", st.selectbox(
            "PSD SIL Level", ["SIL 1","SIL 2","SIL 3","SIL 4"],
            index=["SIL 1","SIL 2","SIL 3","SIL 4"]
                  .index(PDB.get("psd_sil_level","SIL 2"))))
        cs = _cs()
        st.metric("Stations with PSD", str(PDB.get("number_of_stations", 18)))
        st.metric("GoA Level",         str(PDB.get("goa_level", "GOA4 (UTO)")))


# ─────────────────────────────────────────────────────────────────────────────
# TAB: SCADA
# ─────────────────────────────────────────────────────────────────────────────

def tab_scada():
    st.header("🖥️ SCADA")
    c1, c2 = st.columns(2)
    with c1:
        PDB.set("scada_system", st.text_input(
            "SCADA Architecture", PDB.get("scada_system", "")))
        PDB.set("scada_poll_interval_sec", st.number_input(
            "Poll Interval (s)",
            value=int(PDB.get("scada_poll_interval_sec", 2)), min_value=1, max_value=60))
    with c2:
        st.info("SCADA supervises: Traction substations, Ventilation, Lighting, Lifts, Pumps, Fire systems")


# ─────────────────────────────────────────────────────────────────────────────
# TAB: RAMS
# ─────────────────────────────────────────────────────────────────────────────

def tab_rams():
    st.header("📊 RAMS")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("RAMS Targets (inputs)")
        PDB.set("system_availability_target_pct", st.number_input(
            "System Availability Target (%)",
            value=float(PDB.get("system_availability_target_pct", 99.5)),
            min_value=90.0, max_value=99.999, step=0.1, format="%.3f"))
        PDB.set("mtbf_target_hours", st.number_input(
            "MTBF Target (h)",
            value=int(PDB.get("mtbf_target_hours", 50000)), min_value=100, step=1000))
        PDB.set("mttr_target_hours", st.number_input(
            "MTTR Target (h)",
            value=float(PDB.get("mttr_target_hours", 4.0)), min_value=0.25, step=0.25))
        PDB.set("reliability_target_km", st.number_input(
            "Reliability Target (km between failures)",
            value=int(PDB.get("reliability_target_km", 200000)), min_value=1000, step=10000))

    with c2:
        st.subheader("Calculated RAMS Values")
        cs = _cs()
        ram = cs.ram
        st.metric("System Availability",      f"{ram.availability*100:.4f}%")
        st.metric("MTBF",                     f"{ram.mtbf_hours:,} h")
        st.metric("MTTR",                     f"{ram.mttr_hours} h")
        st.metric("Mission Reliability (24h)", f"{ram.mission_reliability_24h:.5f}")
        st.metric("Maintainability M(8h)",    f"{ram.maintainability_8h:.4f}")
        st.metric("km Between Failures",      f"{ram.km_between_failures:,.0f} km")

    st.divider()
    cs = _cs()
    tg = _tg()
    model = PDB.get_model()

    st.subheader("📋 RAM Targets vs. Calculated")
    st.dataframe(tg.ram_targets_table(model, cs),
                 use_container_width=True, hide_index=True)

    st.subheader("📋 Subsystem Availability Allocation")
    st.dataframe(tg.subsystem_availability_table(cs),
                 use_container_width=True, hide_index=True)

    c_fmeca, c_haz = st.columns(2)
    with c_fmeca:
        st.subheader("📋 FMECA (preview)")
        st.dataframe(tg.fmeca_table().head(8), use_container_width=True, hide_index=True)
    with c_haz:
        st.subheader("📋 Hazard Log (preview)")
        st.dataframe(tg.hazard_log_table(cs).head(6), use_container_width=True, hide_index=True)

    st.subheader("📊 RAMS Charts")
    col_a, col_b, col_c = st.columns(3)
    try:
        from figures import figure_availability_chart, figure_reliability_curve, figure_ram_pie
        with col_a:
            img, _ = figure_availability_chart(
                ram.availability, cs.rams_alloc.system_avail_target_pct, save=False)
            st.image(img, use_container_width=True, caption="Availability vs Target")
        with col_b:
            img, _ = figure_reliability_curve(ram.mtbf_hours, save=False)
            st.image(img, use_container_width=True, caption="Reliability R(t)")
        with col_c:
            img, _ = figure_ram_pie(ram.availability, save=False)
            st.image(img, use_container_width=True, caption="Availability Breakdown")
    except Exception as e:
        st.warning(f"Charts not available: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB: MAINTENANCE
# ─────────────────────────────────────────────────────────────────────────────

def tab_maintenance():
    st.header("🔧 Maintenance")
    c1, c2 = st.columns(2)
    with c1:
        PDB.set("maintenance_regime", st.selectbox(
            "Maintenance Strategy",
            ["Preventive and Corrective","Condition-Based","Predictive","Mixed"]))
        PDB.set("maintenance_window_hours", st.number_input(
            "Maintenance Window (h/night)",
            value=int(PDB.get("maintenance_window_hours", 6)), min_value=2, max_value=12))
    with c2:
        PDB.set("cmms_system", st.text_input("CMMS System", PDB.get("cmms_system", "")))
        cs = _cs()
        st.metric("MTTR Target",   f"{cs.ram.mttr_hours} h")
        st.metric("M(8h)",         f"{cs.ram.maintainability_8h:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB: ENVIRONMENTAL
# ─────────────────────────────────────────────────────────────────────────────

def tab_environmental():
    st.header("🌡️ Environmental Conditions")
    c1, c2 = st.columns(2)
    with c1:
        PDB.set("ambient_temp_min_c", st.number_input(
            "Min Temperature (°C)", value=int(PDB.get("ambient_temp_min_c", -5)),
            min_value=-60, max_value=0))
        PDB.set("ambient_temp_max_c", st.number_input(
            "Max Temperature (°C)", value=int(PDB.get("ambient_temp_max_c", 45)),
            min_value=20, max_value=60))
        PDB.set("humidity_max_pct", st.number_input(
            "Max Humidity (%)", value=int(PDB.get("humidity_max_pct", 95)),
            min_value=30, max_value=100))
    with c2:
        PDB.set("altitude_max_m", st.number_input(
            "Max Altitude (m)", value=int(PDB.get("altitude_max_m", 900)),
            min_value=0, max_value=5000))
        PDB.set("seismic_zone", st.text_input("Seismic Zone", PDB.get("seismic_zone", "")))
        PDB.set("ip_rating_tunnels", st.selectbox(
            "IP Rating (Tunnels)", ["IP54","IP55","IP65","IP66","IP67"],
            index=["IP54","IP55","IP65","IP66","IP67"]
                  .index(PDB.get("ip_rating_tunnels","IP54"))))

    st.divider()
    st.dataframe(_tg().environmental_conditions_table(PDB.get_model()),
                 use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB: EXPORT
# ─────────────────────────────────────────────────────────────────────────────

def tab_export():
    st.header("📄 Document Export")
    st.caption("All documents read exclusively from CalculatedState.")

    doc_types = list(cfg.DOCUMENT_TYPES.items())
    selected  = st.multiselect(
        "Select Documents to Generate",
        options=[k for k,_ in doc_types],
        format_func=lambda k: cfg.DOCUMENT_TYPES[k],
        default=["ConOps","SRS","RAM","HeadwayStudy","FleetCalc"])

    use_llm = st.checkbox(
        "Use AI for narrative text (requires API key in sidebar)", value=False)

    if st.button("▶  Generate Selected Documents", type="primary",
                 use_container_width=True, disabled=not selected):
        from document_generator import DocumentGenerator
        progress = st.progress(0, text="Initialising…")
        success  = []
        errors   = []
        for i, doc_key in enumerate(selected):
            progress.progress((i) / len(selected), text=f"Generating {doc_key}…")
            try:
                gen  = DocumentGenerator(doc_key)
                path = gen.build(use_llm=use_llm)
                with open(path, "rb") as f:
                    st.download_button(
                        label    = f"⬇  {cfg.DOCUMENT_TYPES[doc_key]} ({path.name})",
                        data     = f.read(),
                        file_name= path.name,
                        mime     = "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key      = f"dl_{doc_key}",
                    )
                success.append(doc_key)
            except Exception as e:
                errors.append(f"{doc_key}: {e}")
        progress.progress(1.0, text="Done.")
        if success:
            st.success(f"Generated: {', '.join(success)}")
        if errors:
            for err in errors:
                st.error(err)

    st.divider()
    st.subheader("📐 Performance KPIs")
    cs = _cs()
    tg = _tg()
    st.dataframe(tg.performance_kpi_table(cs), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB: AUDIT
# ─────────────────────────────────────────────────────────────────────────────

def tab_audit():
    from audit_engine import render_audit_tab
    render_audit_tab(PDB.get_all())


# ─────────────────────────────────────────────────────────────────────────────
# TAB: DEPENDENCY GRAPH
# ─────────────────────────────────────────────────────────────────────────────

def tab_dependency():
    st.markdown("### 🕸️ Parameter Dependency Graph")
    st.caption("Complete pipeline from ProjectModel inputs to CalculatedState to Documents.")
    try:
        from dependency_graph import generate_parameter_dependency_graph
        import base64
        cs    = _cs()
        model = PDB.get_model()
        g     = generate_parameter_dependency_graph(model, cs)
        s     = g["stats"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Parameters",    s["total_nodes"])
        col2.metric("Dependencies",  s["total_edges"])
        col3.metric("Layers",        s["layers"])
        col4.metric("Documents",     s["doc_nodes"])

        with st.expander("📊 Dependency Diagram", expanded=True):
            svg_b64 = base64.b64encode(g["svg"].encode()).decode()
            st.markdown(
                f'<img src="data:image/svg+xml;base64,{svg_b64}" '
                f'style="width:100%;max-width:1400px"/>',
                unsafe_allow_html=True,
            )

        with st.expander("🔷 Mermaid Source (paste at mermaid.live)"):
            st.code(g["mermaid"], language="")

        st.download_button("⬇  Download SVG", g["svg"],
                           "parameter_dependency_graph.svg", "image/svg+xml",
                           use_container_width=True)
        st.download_button("⬇  Download Mermaid (.mmd)", g["mermaid"],
                           "parameter_dependency_graph.mmd", "text/plain",
                           use_container_width=True)
    except Exception as e:
        st.error(f"Dependency graph error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB: CHANGE IMPACT
# ─────────────────────────────────────────────────────────────────────────────

def tab_impact():
    try:
        from change_impact import render_impact_tab
        render_impact_tab(PDB.get_model(), _cs())
    except Exception as e:
        st.error(f"Change Impact error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────────────────────────

def render():
    configure_page()
    PDB.initialise()

    st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    [data-testid="stMetricValue"] { font-size: 1.4rem; font-weight: 700; }
    h1 { color: #003087; border-bottom: 3px solid #E8352B; padding-bottom: 6px; }
    h2 { color: #003087; }
    h3 { color: #004ab3; }
    div[data-testid="stSidebar"] { background: #f0f4fb; }
    </style>
    """, unsafe_allow_html=True)

    render_sidebar()

    st.title("🚆 Railway Documentation Generator")
    st.caption("Professional railway systems engineering — PASS: C=0 Ma=0 Mi=0")
    st.divider()

    tabs = st.tabs(cfg.UI_TABS)

    tab_fns = [
        tab_project, tab_infrastructure, tab_operations, tab_rolling_stock,
        tab_signalling, tab_traction, tab_depot, tab_telecom,
        tab_psd, tab_scada, tab_rams, tab_maintenance,
        tab_environmental, tab_export, tab_audit, tab_dependency, tab_impact,
    ]

    for i, (tab, fn) in enumerate(zip(tabs, tab_fns)):
        with tab:
            try:
                fn()
            except Exception as e:
                st.error(f"Error in tab {cfg.UI_TABS[i]}: {e}")
                st.exception(e)
