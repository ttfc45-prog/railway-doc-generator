"""
ui.py
Railway Documentation Generator - Streamlit User Interface
All tabs, forms, calculation displays, and export controls.
"""

import streamlit as st
import pandas as pd
import os
from pathlib import Path

import config as cfg
from project_database import ProjectDatabase as PDB
from project_model import ProjectModel
from calculations import RailwayCalculations, CalculationEngine
from tables import TableGenerator
from excel_import import DataImporter


# ═══════════════════════════════════════════════════════════════
# PAGE CONFIG  (must be first Streamlit call)
# ═══════════════════════════════════════════════════════════════

def configure_page():
    st.set_page_config(
        page_title="Railway Documentation Generator",
        page_icon="🚆",
        layout="wide",
        initial_sidebar_state="expanded",
    )


# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/Logo-metro-paris.svg/200px-Logo-metro-paris.svg.png",
                 width=60)
        st.title("RDG")
        st.caption("Railway Documentation Generator")
        st.divider()

        # Save / Load
        st.subheader("💾 Project File")
        if st.button("💾 Save Project", use_container_width=True):
            path = PDB.save_to_file()
            st.success(f"Saved: {path.name}")

        st.divider()

        # Import
        st.subheader("📥 Import Data")
        uploaded = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"],
                                     label_visibility="collapsed")
        if uploaded:
            if uploaded.name.endswith(".csv"):
                data = DataImporter.import_from_csv(uploaded)
            else:
                data = DataImporter.import_from_excel(uploaded)
            n, warns = DataImporter.apply_to_db(data)
            st.success(f"Imported {n} parameters")
            for w in warns:
                st.warning(w)

        template_bytes = DataImporter.generate_import_template()
        st.download_button("📄 Download Import Template", template_bytes,
                            file_name="rdg_import_template.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True)

        st.divider()
        st.subheader("🔑 AI Settings")
        provider = st.selectbox("AI Provider", ["anthropic", "openai", "none"],
                                 index=["anthropic", "openai", "none"].index(cfg.AI_PROVIDER))
        cfg.AI_PROVIDER = provider
        if provider != "none":
            key_env = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
            api_key = st.text_input(f"{provider.title()} API Key",
                                     value=os.environ.get(key_env, ""),
                                     type="password")
            if api_key:
                os.environ[key_env] = api_key

        st.divider()
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            PDB.reset_to_defaults()
            st.rerun()

        st.caption("v1.0 | © 2025 RDG")


# ═══════════════════════════════════════════════════════════════
# TAB: PROJECT INFORMATION
# ═══════════════════════════════════════════════════════════════

def tab_project():
    st.header("🏗️ Project Information")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Identity")
        PDB.set("project_name",   st.text_input("Project Name",   PDB.get("project_name")))
        PDB.set("country",        st.text_input("Country",        PDB.get("country")))
        PDB.set("client",         st.text_input("Client",         PDB.get("client")))
        PDB.set("consultant",     st.text_input("Consultant",     PDB.get("consultant")))
        PDB.set("line_name",      st.text_input("Line Name",      PDB.get("line_name")))
        PDB.set("document_number",st.text_input("Document Number",PDB.get("document_number")))
        PDB.set("revision",       st.text_input("Revision",       PDB.get("revision")))
        PDB.set("status",         st.selectbox("Status",
            ["Draft","For Review","For Approval","Approved","Superseded"],
            index=["Draft","For Review","For Approval","Approved","Superseded"].index(
                PDB.get("status","Draft"))))

    with c2:
        st.subheader("Standards & Lifecycle")
        PDB.set("project_life_years", st.number_input("Project Life (years)",
            value=int(PDB.get("project_life_years", 40)), min_value=10, max_value=100))
        PDB.set("warranty_years", st.number_input("Warranty Period (years)",
            value=int(PDB.get("warranty_years", 2)), min_value=1, max_value=10))
        PDB.set("maintenance_regime", st.selectbox("Maintenance Regime",
            ["Preventive and Corrective","Condition-Based","Predictive","Total Productive Maintenance"],
            index=0))
        st.subheader("Applicable Standards")
        standards_text = "\n".join(PDB.get("design_standards", []))
        new_standards = st.text_area("Standards (one per line)", standards_text, height=150)
        PDB.set("design_standards", [s.strip() for s in new_standards.split("\n") if s.strip()])

    st.divider()
    st.subheader("📊 Project Summary")
    summary = PDB.as_summary_dict()
    df_sum  = pd.DataFrame(list(summary.items()), columns=["Parameter", "Value"])
    st.dataframe(df_sum, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# TAB: INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════

def tab_infrastructure():
    st.header("🛤️ Infrastructure")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Alignment")
        PDB.set("line_length_km",    st.number_input("Line Length (km)",
            value=float(PDB.get("line_length_km", 22.5)), min_value=0.1, step=0.5))
        PDB.set("number_of_stations",st.number_input("Number of Stations",
            value=int(PDB.get("number_of_stations", 18)), min_value=2, max_value=100))
        PDB.set("depot_location",    st.text_input("Depot Location", PDB.get("depot_location")))
        PDB.set("number_of_tracks",  st.selectbox("Number of Tracks", [1, 2, 3, 4],
            index=[1,2,3,4].index(int(PDB.get("number_of_tracks", 2)))))
        PDB.set("track_gauge_mm",    st.selectbox("Track Gauge (mm)",
            [600, 750, 900, 1000, 1067, 1200, 1435, 1520, 1600, 1668],
            index=[600, 750, 900, 1000, 1067, 1200, 1435, 1520, 1600, 1668].index(
                int(PDB.get("track_gauge_mm", 1435)))))
        PDB.set("loading_gauge",     st.text_input("Loading Gauge", PDB.get("loading_gauge", "UIC 505-1")))

    with c2:
        st.subheader("Station List")
        stations = PDB.get_station_list()
        station_text = "\n".join(stations)
        new_stations = st.text_area("Station Names (one per line)", station_text, height=300)
        stn_list = [s.strip() for s in new_stations.split("\n") if s.strip()]
        PDB.set("station_list", stn_list)
        if stn_list:
            PDB.set("number_of_stations", len(stn_list))
        st.info(f"Total stations: {len(stn_list)}")


# ═══════════════════════════════════════════════════════════════
# TAB: OPERATIONS
# ═══════════════════════════════════════════════════════════════

def tab_operations():
    st.header("🚆 Operations")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Speed & Timing")
        PDB.set("max_speed_kmh",      st.number_input("Max Speed (km/h)",
            value=int(PDB.get("max_speed_kmh", 80)), min_value=20, max_value=350))
        PDB.set("design_speed_kmh",   st.number_input("Design Speed (km/h)",
            value=int(PDB.get("design_speed_kmh", 90)), min_value=20, max_value=400))
        PDB.set("station_dwell_sec",  st.slider("Station Dwell (s)",
            min_value=15, max_value=120, value=int(PDB.get("station_dwell_sec", 35))))
        PDB.set("terminal_dwell_min", st.number_input("Terminal Dwell (min)",
            value=float(PDB.get("terminal_dwell_min", 3.0)), min_value=0.5, step=0.5))
        PDB.set("peak_headway_sec",   st.slider("Peak Headway (s)",
            min_value=60, max_value=600, value=int(PDB.get("peak_headway_sec", 120)), step=30))
        PDB.set("off_peak_headway_sec",st.slider("Off-Peak Headway (s)",
            min_value=60, max_value=1200, value=int(PDB.get("off_peak_headway_sec", 300)), step=60))

    with c2:
        st.subheader("Service Parameters")
        PDB.set("operating_hours_per_day", st.number_input("Operating Hours/Day",
            value=int(PDB.get("operating_hours_per_day", 18)), min_value=1, max_value=24))
        PDB.set("peak_demand_pphpd",  st.number_input("Peak Demand (pphpd)",
            value=int(PDB.get("peak_demand_pphpd", 45000)), min_value=1000, step=1000))
        PDB.set("daily_passengers",   st.number_input("Daily Passengers",
            value=int(PDB.get("daily_passengers", 500000)), min_value=1000, step=10000))
        PDB.set("goa_level",          st.selectbox("Grade of Automation",
            ["GOA1 (Manual)", "GOA2 (STO)", "GOA3 (DTO)", "GOA4 (UTO)"],
            index=3))

    st.divider()
    st.subheader("⚙️ Live Calculations")
    with st.spinner("Computing…"):
        cs = CalculationEngine.run(PDB.get_model())
        ops = cs.ops

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Commercial Speed",   f"{ops.commercial_speed_kmh:.1f} km/h")
    col2.metric("Round Trip Time",    f"{ops.round_trip_time_min:.0f} min")
    col3.metric("Trains in Service",  str(ops.trains_in_service))
    col4.metric("Total Fleet",        str(ops.total_fleet))

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Capacity (4 pax/m²)", f"{ops.pphpd_4ppm2:,} pphpd")
    col6.metric("Capacity (6 pax/m²)", f"{ops.pphpd_6ppm2:,} pphpd")
    col7.metric("Daily Train-km",      f"{ops.daily_train_km:,.0f}")
    col8.metric("Annual Train-km",     f"{ops.annual_train_km:,.0f}")

    with st.expander("📋 Full Operational Parameters Table"):
        tg = TableGenerator()
        st.dataframe(tg.operational_parameters_table(PDB.get_all(), ops),
                     use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# TAB: ROLLING STOCK
# ═══════════════════════════════════════════════════════════════

def tab_rolling_stock():
    st.header("🚃 Rolling Stock")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Consist")
        PDB.set("cars_per_train",   st.slider("Cars per Train",
            min_value=1, max_value=10, value=int(PDB.get("cars_per_train", 6))))
        PDB.set("train_length_m",   st.number_input("Train Length (m)",
            value=float(PDB.get("train_length_m", 138.0)), min_value=20.0, step=1.0))
        PDB.set("train_width_m",    st.number_input("Train Width (m)",
            value=float(PDB.get("train_width_m", 2.88)), min_value=2.0, max_value=3.5, step=0.01))
        PDB.set("train_height_m",   st.number_input("Train Height (m)",
            value=float(PDB.get("train_height_m", 3.70)), min_value=2.5, max_value=5.0, step=0.01))

        st.subheader("Performance")
        PDB.set("max_acceleration_mss",     st.number_input("Max Acceleration (m/s²)",
            value=float(PDB.get("max_acceleration_mss", 1.0)), min_value=0.5, max_value=2.0, step=0.05))
        PDB.set("max_deceleration_mss",     st.number_input("Service Deceleration (m/s²)",
            value=float(PDB.get("max_deceleration_mss", 1.0)), min_value=0.5, max_value=2.0, step=0.05))
        PDB.set("emergency_deceleration_mss",st.number_input("Emergency Deceleration (m/s²)",
            value=float(PDB.get("emergency_deceleration_mss", 1.3)), min_value=0.8, max_value=3.0, step=0.05))

    with c2:
        st.subheader("Capacity")
        PDB.set("seated_capacity",           st.number_input("Seated Capacity",
            value=int(PDB.get("seated_capacity", 306)), min_value=50, step=10))
        PDB.set("standing_capacity_4ppm2",   st.number_input("Standing at 4 pax/m²",
            value=int(PDB.get("standing_capacity_4ppm2", 612)), min_value=50, step=10))
        PDB.set("standing_capacity_6ppm2",   st.number_input("Standing at 6 pax/m²",
            value=int(PDB.get("standing_capacity_6ppm2", 918)), min_value=50, step=10))
        total_6 = PDB.get("seated_capacity", 306) + PDB.get("standing_capacity_6ppm2", 918)
        # total_capacity_6ppm2 is a calculated value — not stored in PDB
        st.info(f"Total Capacity (6 pax/m²): **{total_6}** passengers per train")

        st.subheader("Fleet")
        # fleet_size is a calculated output — display only (do not store)
        # (value shown in Operations tab metrics from CalculationEngine)
        st.info("Fleet size is calculated by the engine from RTT and headway — see Operations tab.")
        _removed_fleet_size = st.number_input("Operational Fleet",
            value=int(PDB.get("fleet_required", 38) if PDB.get("fleet_required") else 38), min_value=1, step=1)
        _removed_reserve_fleet = st.number_input("Reserve Fleet",
            value=4, min_value=0, step=1)
        _cs_rs = CalculationEngine.run(PDB.get_model())
        st.info(f"Total Fleet (calculated): **{_cs_rs.ops.total_fleet}** trains")

    st.divider()
    with st.expander("📋 Rolling Stock Data Table"):
        tg = TableGenerator()
        _cs_rst = CalculationEngine.run(PDB.get_model())
        st.dataframe(tg.rolling_stock_table(PDB.get_model(), _cs_rst),
                     use_container_width=True, hide_index=True)

    with st.expander("📋 Fleet Calculation Table"):
        cs = CalculationEngine.run(PDB.get_model())
        ops = cs.ops
        st.dataframe(tg.fleet_calculation_table(PDB.get_model(), cs),
                     use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# TAB: SIGNALLING
# ═══════════════════════════════════════════════════════════════

def tab_signalling():
    st.header("🚦 Signalling & Train Control")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("System Type")
        sig_type = st.selectbox("Signalling System", [
            "CBTC Moving Block", "CBTC Fixed Block",
            "ETCS Level 2", "ETCS Level 3",
            "Conventional Fixed Block with ATC"
        ], index=0)
        PDB.set("signalling_system", sig_type)
        PDB.set("safety_integrity_level", st.selectbox("Safety Integrity Level",
            ["SIL 1", "SIL 2", "SIL 3", "SIL 4"], index=3))
        PDB.set("atc_vendor", st.text_input("ATC Vendor (if known)", PDB.get("atc_vendor", "TBD")))

    with c2:
        st.subheader("Headway")
        # technical_headway_sec is a calculated output — display only
        st.info("Technical headway is calculated from max speed and emergency deceleration — see below.")
        _removed_technical_headway = st.number_input("Technical Headway (s) [calculated — read only]",
            value=int(PDB.get("headway_technical_sec", 90)), min_value=30, max_value=600)

    st.divider()
    st.subheader("⚙️ Headway Calculation")
    p = PDB.get_all()
    _cs_sig = CalculationEngine.run(PDB.get_model())
    hw = _cs_sig.headway

    c1, c2, c3 = st.columns(3)
    c1.metric("Technical Headway",    f"{hw.technical_headway_sec:.1f} s")
    c2.metric("Commercial Headway",   f"{hw.commercial_headway_sec:.1f} s")
    c3.metric("Min Safe Separation",  f"{hw.minimum_safe_separation_m:.0f} m")

    with st.expander("📋 Headway Breakdown Table"):
        tg = TableGenerator()
        st.dataframe(tg.headway_breakdown_table(hw), use_container_width=True, hide_index=True)

    st.subheader("📊 Headway Chart")
    from figures import figure_headway_breakdown
    img_bytes, _ = figure_headway_breakdown(hw.headway_breakdown, save=False)
    st.image(img_bytes, use_column_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB: TRACTION POWER
# ═══════════════════════════════════════════════════════════════

def tab_traction():
    st.header("⚡ Traction Power")
    c1, c2 = st.columns(2)

    with c1:
        PDB.set("power_supply_voltage", st.selectbox("Supply Voltage",
            ["750 Vdc", "1500 Vdc", "3000 Vdc", "25 kVac", "15 kVac"], index=1))
        PDB.set("power_supply_type", st.selectbox("Distribution Type", [
            "Overhead Catenary System (OCS)",
            "Third Rail (Top Contact)",
            "Third Rail (Bottom Contact)",
            "Rigid Overhead Conductor Rail",
        ], index=0))
        PDB.set("substation_spacing_km", st.number_input("Substation Spacing (km)",
            value=float(PDB.get("substation_spacing_km", 2.5)), min_value=0.5, step=0.5))
        PDB.set("number_of_substations", st.number_input("Number of Substations",
            value=int(PDB.get("number_of_substations", 10)), min_value=1, step=1))
        PDB.set("regenerative_braking", st.checkbox("Regenerative Braking",
            value=PDB.get("regenerative_braking", True)))

    with c2:
        _cs_tr = CalculationEngine.run(PDB.get_model())
        tr = _cs_tr.traction
        st.subheader("Calculated Values")
        st.metric("Peak Power per Train", f"{tr.peak_power_kw:,.0f} kW")
        st.metric("Average Power per Train", f"{tr.average_power_kw:,.0f} kW")
        st.metric("Energy per Train-km", f"{tr.energy_per_train_km_kwh:.2f} kWh/km")
        st.metric("Substation Rating", f"{tr.substation_rating_mva:.1f} MVA")
        st.metric("Annual Energy", f"{tr.annual_energy_mwh:,.0f} MWh")
        st.metric("Regenerative Saving", f"{tr.regenerative_saving_pct:.1f}%")


# ═══════════════════════════════════════════════════════════════
# TAB: DEPOT
# ═══════════════════════════════════════════════════════════════

def tab_depot():
    st.header("🏭 Depot")
    c1, c2 = st.columns(2)
    with c1:
        PDB.set("depot_location", st.text_input("Depot Location", PDB.get("depot_location")))
        PDB.set("depot_stabling_tracks", st.number_input("Stabling Tracks",
            value=int(PDB.get("depot_stabling_tracks", 8)), min_value=1, step=1))
        PDB.set("depot_maintenance_tracks", st.number_input("Maintenance Roads",
            value=int(PDB.get("depot_maintenance_tracks", 4)), min_value=1, step=1))
        PDB.set("depot_wash_roads", st.number_input("Wash Roads",
            value=int(PDB.get("depot_wash_roads", 2)), min_value=1, step=1))
    with c2:
        PDB.set("depot_has_wheel_lathe", st.checkbox("Wheel Lathe",
            value=PDB.get("depot_has_wheel_lathe", True)))
        PDB.set("depot_has_lifting_jacks", st.checkbox("Train Lifting Jacks",
            value=PDB.get("depot_has_lifting_jacks", True)))
        PDB.set("depot_has_test_track", st.checkbox("Test Track",
            value=PDB.get("depot_has_test_track", True)))
        PDB.set("depot_capacity_trains", st.number_input("Depot Capacity (trains)",
            value=int(PDB.get("depot_capacity_trains", 45)), min_value=1, step=1))
    st.info("The Depot Operation Concept document provides the full operational description of the depot facility.")


# ═══════════════════════════════════════════════════════════════
# TAB: TELECOMMUNICATIONS
# ═══════════════════════════════════════════════════════════════

def tab_telecom():
    st.header("📡 Telecommunications")
    default_systems = PDB.get("telecom_systems", [])
    options = ["TETRA Radio", "CCTV", "Public Address", "Passenger Information System",
               "Clocks", "Telephone Network", "SCADA Communication",
               "LAN/WAN Backbone", "CBTC Radio", "Passenger WiFi",
               "Emergency Telephone (EET)", "Ticketing Network"]
    selected = st.multiselect("Active Telecommunications Systems", options,
                               default=default_systems)
    PDB.set("telecom_systems", selected)

    c1, c2 = st.columns(2)
    with c1:
        PDB.set("telecom_backbone", st.selectbox("Backbone Technology",
            ["Ethernet/MPLS", "SDH", "CWDM", "DWDM"], index=0))
        PDB.set("telecom_radio_system", st.selectbox("Operational Radio",
            ["TETRA", "DMR", "TEDS", "LTE", "5G", "Analogue VHF"], index=0))
    with c2:
        PDB.set("cctv_resolution", st.selectbox("CCTV Resolution",
            ["HD 1080p", "4K", "HD 720p", "SD"], index=0))
        PDB.set("pa_sti_target", st.number_input("PA STI Target", value=0.55,
            min_value=0.4, max_value=1.0, step=0.05))


# ═══════════════════════════════════════════════════════════════
# TAB: PLATFORM SCREEN DOORS
# ═══════════════════════════════════════════════════════════════

def tab_psd():
    st.header("🚪 Platform Screen Doors")
    c1, c2 = st.columns(2)
    with c1:
        PDB.set("psd_type", st.selectbox("PSD Type",
            ["Full-Height PSD", "Half-Height PSD", "Sliding Platform Doors",
             "Platform Edge Doors (PED)"], index=0))
        PDB.set("psd_door_width_mm", st.number_input("Door Opening Width (mm)",
            value=int(PDB.get("psd_door_width_mm", 1400)), min_value=800, step=50))
        PDB.set("psd_door_height_mm", st.number_input("Door Height (mm)",
            value=int(PDB.get("psd_door_height_mm", 2400)), min_value=1800, step=100))
        PDB.set("psd_doors_per_car",  st.number_input("Door Pairs per Car Side",
            value=int(PDB.get("psd_doors_per_car", 4)), min_value=2, max_value=8))
    with c2:
        PDB.set("psd_cycle_time_s",   st.number_input("Door Cycle Time (s)",
            value=float(PDB.get("psd_cycle_time_s", 6.0)), min_value=2.0, max_value=15.0, step=0.5))
        PDB.set("psd_sil_level",      st.selectbox("PSD SIL Level",
            ["SIL 1", "SIL 2", "SIL 3", "SIL 4"], index=1))
        PDB.set("psd_emergency_release", st.checkbox("Emergency Manual Release",
            value=PDB.get("psd_emergency_release", True)))


# ═══════════════════════════════════════════════════════════════
# TAB: SCADA
# ═══════════════════════════════════════════════════════════════

def tab_scada():
    st.header("🖥️ SCADA")
    c1, c2 = st.columns(2)
    with c1:
        PDB.set("scada_system",        st.text_input("SCADA Description",
            PDB.get("scada_system", "Centralised SCADA with distributed RTUs")))
        PDB.set("scada_poll_interval_s",st.number_input("RTU Poll Interval (s)",
            value=float(PDB.get("scada_poll_interval_s", 2.0)), min_value=0.5, step=0.5))
        PDB.set("scada_protocol",      st.selectbox("Communication Protocol",
            ["IEC 60870-5-104", "DNP3", "Modbus TCP", "OPC-UA", "IEC 61850"], index=0))
    with c2:
        PDB.set("scada_subsystems",    st.multiselect("SCADA-Controlled Subsystems",
            ["Traction Substations", "Ventilation", "HVAC", "Lighting", "Lifts",
             "Escalators", "Pumping", "Fire Detection", "PSD", "Intruder Alarms"],
            default=PDB.get("scada_subsystems",
                ["Traction Substations", "Ventilation", "HVAC", "Lighting"])))
        PDB.set("scada_cybersecurity", st.selectbox("Cybersecurity Standard",
            ["IEC 62443", "NIST SP 800-82", "ISO 27001"], index=0))


# ═══════════════════════════════════════════════════════════════
# TAB: RAMS
# ═══════════════════════════════════════════════════════════════

def tab_rams():
    st.header("📊 RAMS — Reliability, Availability, Maintainability & Safety")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("RAMS Targets")
        PDB.set("system_availability_target_pct", st.number_input(
            "System Availability Target (%)",
            value=float(PDB.get("system_availability_target_pct", 99.5)),
            min_value=90.0, max_value=99.999, step=0.1, format="%.3f"))
        PDB.set("operational_availability_target_pct", st.number_input(
            "Operational Availability Target (%)",
            value=float(PDB.get("operational_availability_target_pct", 98.0)),
            min_value=80.0, max_value=99.99, step=0.1, format="%.2f"))
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
        _cs_ram = CalculationEngine.run(PDB.get_model())
        ram = _cs_ram.ram
        st.metric("System Availability",   f"{ram.system_availability*100:.4f}%")
        st.metric("MTBF",                  f"{ram.mtbf_hours:,} h")
        st.metric("MTTR",                  f"{ram.mttr_hours} h")
        st.metric("Mission Reliability (24h)", f"{ram.mission_reliability_24h:.4f}")
        st.metric("Maintainability",       f"{ram.maintainability:.4f}")
        st.metric("km Between Failures",   f"{ram.km_between_failures:,.0f} km")

    st.divider()
    st.subheader("📋 RAM Targets Table")
    tg = TableGenerator()
    st.dataframe(tg.ram_targets_table(PDB.get_all(), ram),
                 use_container_width=True, hide_index=True)

    st.subheader("📋 Subsystem Availability Allocation")
    st.dataframe(tg.subsystem_availability_table(),
                 use_container_width=True, hide_index=True)

    c_fmeca, c_haz = st.columns(2)
    with c_fmeca:
        st.subheader("📋 FMECA (preview)")
        st.dataframe(tg.fmeca_table().head(8), use_container_width=True, hide_index=True)
    with c_haz:
        st.subheader("📋 Hazard Log (preview)")
        st.dataframe(tg.hazard_log_table().head(8), use_container_width=True, hide_index=True)

    st.subheader("📊 RAMS Charts")
    col_a, col_b, col_c = st.columns(3)
    from figures import figure_availability_chart, figure_reliability_curve, figure_ram_pie
    with col_a:
        img, _ = figure_availability_chart(ram.system_availability,
                                            PDB.get("system_availability_target_pct", 99.5),
                                            save=False)
        st.image(img, use_column_width=True)
    with col_b:
        img, _ = figure_reliability_curve(ram.mtbf_hours, save=False)
        st.image(img, use_column_width=True)
    with col_c:
        img, _ = figure_ram_pie(ram.system_availability, save=False)
        st.image(img, use_column_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB: MAINTENANCE
# ═══════════════════════════════════════════════════════════════

def tab_maintenance():
    st.header("🔧 Maintenance")
    c1, c2 = st.columns(2)
    with c1:
        PDB.set("maintenance_regime",        st.selectbox("Maintenance Strategy",
            ["Preventive and Corrective", "Condition-Based (CBM)",
             "Reliability-Centred (RCM)", "Total Productive Maintenance (TPM)"], index=0))
        PDB.set("maintenance_cmms",          st.text_input("CMMS Platform",
            PDB.get("maintenance_cmms", "IBM Maximo / SAP PM")))
        PDB.set("maintenance_window_hours",  st.number_input("Maintenance Window (h/day)",
            value=float(PDB.get("maintenance_window_hours", 6.0)), min_value=1.0, max_value=12.0, step=0.5))
    with c2:
        PDB.set("maintenance_levels",        st.multiselect("Maintenance Levels",
            ["Level 1: Line Maintenance", "Level 2: Depot Maintenance",
             "Level 3: Workshop Overhaul", "Level 4: Manufacturer Support"],
            default=PDB.get("maintenance_levels",
                ["Level 1: Line Maintenance", "Level 2: Depot Maintenance",
                 "Level 3: Workshop Overhaul"])))
    st.info("Full maintenance schedule and task lists are generated in the Maintenance Plan document.")


# ═══════════════════════════════════════════════════════════════
# TAB: ENVIRONMENTAL CONDITIONS
# ═══════════════════════════════════════════════════════════════

def tab_environmental():
    st.header("🌡️ Environmental Conditions")
    c1, c2 = st.columns(2)
    with c1:
        PDB.set("ambient_temp_min_c",  st.number_input("Min Ambient Temperature (°C)",
            value=int(PDB.get("ambient_temp_min_c", -5)), min_value=-60, max_value=0))
        PDB.set("ambient_temp_max_c",  st.number_input("Max Ambient Temperature (°C)",
            value=int(PDB.get("ambient_temp_max_c", 45)), min_value=20, max_value=70))
        PDB.set("humidity_max_pct",    st.slider("Max Relative Humidity (%)",
            min_value=50, max_value=100, value=int(PDB.get("humidity_max_pct", 95))))
        PDB.set("altitude_max_m",      st.number_input("Max Altitude (m)",
            value=int(PDB.get("altitude_max_m", 900)), min_value=0, step=100))
    with c2:
        PDB.set("seismic_zone",        st.selectbox("Seismic Zone",
            ["None", "Zone 1", "Zone 2A", "Zone 2B", "Zone 3", "Zone 4"], index=4))
        PDB.set("ip_rating_tunnels",   st.selectbox("IP Rating (Tunnels)",
            ["IP54", "IP55", "IP65", "IP67", "IP68"], index=0))
        PDB.set("ip_rating_outdoor",   st.selectbox("IP Rating (Outdoor)",
            ["IP54", "IP55", "IP65", "IP67", "IP68"], index=2))
    st.divider()
    tg = TableGenerator()
    st.dataframe(tg.environmental_conditions_table(PDB.get_all()),
                 use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# TAB: EXPORT
# ═══════════════════════════════════════════════════════════════

def tab_export():
    st.header("📄 Export Documents")

    from config import DOCUMENT_TYPES
    from document_generator import DocumentGenerator

    st.subheader("Select Documents to Generate")

    # All 32 document types in a multiselect
    all_keys  = list(DOCUMENT_TYPES.keys())
    all_labels= [f"{k} — {v}" for k, v in DOCUMENT_TYPES.items()]
    selected_labels = st.multiselect(
        "Documents",
        options=all_labels,
        default=all_labels[:3],
    )
    selected_keys = [all_keys[all_labels.index(lbl)] for lbl in selected_labels]

    use_llm = st.checkbox(
        "✨ Use AI to generate chapter text (requires API key)",
        value=bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY"))
    )

    col_docx, col_excel = st.columns(2)

    with col_docx:
        if st.button("📝 Generate Word (.docx)", type="primary",
                     disabled=len(selected_keys) == 0, use_container_width=True):
            generated = []
            progress = st.progress(0)
            status   = st.empty()

            for doc_idx, doc_key in enumerate(selected_keys):
                status.text(f"Building {DOCUMENT_TYPES[doc_key]}…")
                gen = DocumentGenerator(doc_key)

                def cb(pct, msg, _di=doc_idx, _n=len(selected_keys)):
                    progress.progress((_di + pct) / _n, msg)

                path = gen.build(use_llm=use_llm, progress_cb=cb)
                generated.append(path)

            progress.empty()
            status.empty()
            st.success(f"✅ Generated {len(generated)} document(s)")

            for path in generated:
                with open(path, "rb") as f:
                    st.download_button(
                        f"⬇️ {path.name}",
                        f.read(),
                        file_name=path.name,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=str(path),
                    )

    with col_excel:
        if st.button("📊 Generate Excel Workbook", type="secondary",
                     disabled=len(selected_keys) == 0, use_container_width=True):
            doc_key = selected_keys[0] if selected_keys else "BOD"
            gen  = DocumentGenerator(doc_key)
            path = gen.build_excel()
            with open(path, "rb") as f:
                st.download_button(
                    f"⬇️ {path.name}",
                    f.read(),
                    file_name=path.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="excel_dl",
                )

    st.divider()
    st.subheader("📊 Performance KPIs Preview")
    _cs_exp = CalculationEngine.run(PDB.get_model())
    kpis = {k:v for k,v in [
        ("Commercial Speed (km/h)", f"{_cs_exp.ops.commercial_speed_kmh:.1f}"),
        ("Total Fleet", str(_cs_exp.ops.total_fleet)),
        ("PPHPD (6 pax/m²)", f"{_cs_exp.capacity.pphpd_6ppm2:,}"),
        ("Annual Train-km", f"{_cs_exp.ops.annual_train_km:,.0f}"),
        ("System Availability (%)", f"{_cs_exp.ram.availability*100:.4f}"),
        ("km Between Failures", f"{_cs_exp.ram.km_between_failures:,.0f}"),
    ]}
    df_kpi = pd.DataFrame(list(kpis.items()), columns=["KPI", "Value"])
    st.dataframe(df_kpi, use_container_width=True, hide_index=True)

    st.subheader("📊 Charts Preview")
    p   = PDB.get_all()
    _cs_fig = CalculationEngine.run(PDB.get_model())
    ops = _cs_fig.ops
    ram = _cs_fig.ram
    hw  = _cs_fig.headway

    from figures import (figure_fleet_composition, figure_train_capacity,
                         figure_speed_comparison, figure_capacity_demand)

    col1, col2 = st.columns(2)
    with col1:
        img, _ = figure_fleet_composition(ops.fleet_required, ops.reserve_trains, save=False)
        st.image(img, caption="Fleet Composition", use_column_width=True)
        img, _ = figure_speed_comparison(ops.commercial_speed_kmh,
                                          p.get("max_speed_kmh", 80),
                                          p.get("design_speed_kmh", 90), save=False)
        st.image(img, caption="Speed Comparison", use_column_width=True)
    with col2:
        img, _ = figure_train_capacity(p.get("seated_capacity", 306),
                                        p.get("standing_capacity_4ppm2", 612),
                                        p.get("standing_capacity_6ppm2", 918), save=False)
        st.image(img, caption="Train Capacity", use_column_width=True)
        img, _ = figure_capacity_demand(p.get("peak_demand_pphpd", 45000),
                                         ops.pphpd_4ppm2, ops.pphpd_6ppm2, save=False)
        st.image(img, caption="Capacity vs Demand", use_column_width=True)


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER
# ═══════════════════════════════════════════════════════════════

def render():
    configure_page()
    PDB.initialise()

    # Custom CSS
    st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    [data-testid="stMetricValue"] { font-size: 1.4rem; font-weight: 700; }
    [data-testid="stMetricLabel"] { font-size: 0.78rem; color: #555; }
    h1 { color: #003087; border-bottom: 3px solid #E8352B; padding-bottom: 6px; }
    h2 { color: #003087; }
    h3 { color: #004ab3; }
    div[data-testid="stSidebar"] { background: #f0f4fb; }
    .stSelectbox label, .stTextInput label, .stNumberInput label { font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

    render_sidebar()

    st.title("🚆 Railway Documentation Generator")
    st.caption("Professional railway systems engineering document automation")
    st.divider()

    tabs = st.tabs(cfg.UI_TABS)

    with tabs[0]:  tab_project()
    with tabs[1]:  tab_infrastructure()
    with tabs[2]:  tab_operations()
    with tabs[3]:  tab_rolling_stock()
    with tabs[4]:  tab_signalling()
    with tabs[5]:  tab_traction()
    with tabs[6]:  tab_depot()
    with tabs[7]:  tab_telecom()
    with tabs[8]:  tab_psd()
    with tabs[9]:  tab_scada()
    with tabs[10]: tab_rams()
    with tabs[11]: tab_maintenance()
    with tabs[12]: tab_environmental()
    with tabs[13]: tab_export()
    with tabs[14]:
        from audit_engine import render_audit_tab
        render_audit_tab(PDB.get_all())
    with tabs[15]:
        _model = PDB.get_model()
        from calculations import CalculationEngine as _CE
        _cs15 = _CE.run(_model)
        from dependency_graph import generate_parameter_dependency_graph
        import streamlit as _st
        _st.markdown("### Parameter Dependency Graph")
        _st.caption("Full pipeline from ProjectModel inputs to CalculatedState to Documents.")
        _g = generate_parameter_dependency_graph(_model, _cs15)
        _st.json({k:v for k,v in _g["stats"].items()})
        _st.markdown("#### Mermaid Source")
        _st.code(_g["mermaid"], language="")
        _st.markdown("#### SVG")
        _st.components.v1.html(_g["svg"], height=600, scrolling=True)
        _st.download_button("⬇  Download SVG", _g["svg"],
            file_name="parameter_dependency_graph.svg", mime="image/svg+xml")
        _st.download_button("⬇  Download Mermaid (.mmd)", _g["mermaid"],
            file_name="parameter_dependency_graph.mmd", mime="text/plain")
    with tabs[16]:
        _model2 = PDB.get_model()
        from calculations import CalculationEngine as _CE2
        _cs16 = _CE2.run(_model2)
        from change_impact import render_impact_tab
        render_impact_tab(_model2, _cs16)
