"""
templates.py
Railway Documentation Generator - Document Structure Templates
Defines the chapter/section hierarchy for every supported document type.
"""

# Each template is a list of sections; each section is a dict:
#   title        : heading text
#   level        : 1 = H1, 2 = H2, 3 = H3
#   generator    : key into CHAPTER_GENERATORS (llm_writer.py)
#   tables       : list of table generator method names (tables.py)
#   figures      : list of figure keys (figures.py)
#   static_text  : optional override text (overrides generator)

TEMPLATES: dict[str, list[dict]] = {

    # ───────────────────────────────────────────────
    # 1. CONCEPT OF OPERATIONS (ConOps)
    # ───────────────────────────────────────────────
    "ConOps": [
        {"title": "Introduction",               "level": 1, "generator": "introduction",       "tables": [], "figures": []},
        {"title": "Scope",                       "level": 1, "generator": "scope",              "tables": [], "figures": []},
        {"title": "References",                  "level": 1, "generator": None,                "tables": ["standards_table"], "figures": []},
        {"title": "System Overview",             "level": 1, "generator": "system_overview",   "tables": ["project_data_table"], "figures": ["speed"]},
        {"title": "Alignment Description",       "level": 2, "generator": "alignment",         "tables": [], "figures": []},
        {"title": "Station Description",         "level": 2, "generator": "stations",          "tables": [], "figures": []},
        {"title": "Operations Concept",          "level": 1, "generator": "operations_concept","tables": ["operational_parameters_table"], "figures": ["capacity_demand"]},
        {"title": "Normal Operations",           "level": 2, "generator": "normal_operation",  "tables": [], "figures": ["train_diagram"]},
        {"title": "Degraded Operations",         "level": 2, "generator": "degraded_operation","tables": [], "figures": []},
        {"title": "Emergency Operations",        "level": 2, "generator": "emergency_operation","tables": [], "figures": []},
        {"title": "OCC Operations",              "level": 2, "generator": "occ",               "tables": [], "figures": []},
        {"title": "Rolling Stock",               "level": 1, "generator": "rolling_stock",     "tables": ["rolling_stock_table"], "figures": ["capacity_train"]},
        {"title": "Fleet",                       "level": 2, "generator": None,                "tables": ["fleet_calculation_table"], "figures": ["fleet"]},
        {"title": "Maintenance Concept",         "level": 1, "generator": "maintenance",       "tables": [], "figures": []},
        {"title": "Conclusion",                  "level": 1, "generator": "conclusion",        "tables": [], "figures": []},
    ],

    # ───────────────────────────────────────────────
    # 2. OPERATION CONTROL STRATEGY (OCS)
    # ───────────────────────────────────────────────
    "OCS": [
        {"title": "Introduction",               "level": 1, "generator": "introduction",       "tables": [], "figures": []},
        {"title": "Scope",                       "level": 1, "generator": "scope",              "tables": [], "figures": []},
        {"title": "System Overview",             "level": 1, "generator": "system_overview",   "tables": ["project_data_table"], "figures": []},
        {"title": "OCC Description",             "level": 1, "generator": "occ",               "tables": [], "figures": []},
        {"title": "Normal Operation Strategy",   "level": 1, "generator": "normal_operation",  "tables": ["operational_parameters_table"], "figures": ["train_diagram"]},
        {"title": "Degraded Operation Strategy", "level": 1, "generator": "degraded_operation","tables": [], "figures": []},
        {"title": "Emergency Operation Strategy","level": 1, "generator": "emergency_operation","tables": [], "figures": []},
        {"title": "Signalling Overview",         "level": 1, "generator": "signalling",        "tables": [], "figures": []},
        {"title": "Conclusion",                  "level": 1, "generator": "conclusion",        "tables": [], "figures": []},
    ],

    # ───────────────────────────────────────────────
    # 3. BASIS OF DESIGN (BOD)
    # ───────────────────────────────────────────────
    "BOD": [
        {"title": "Introduction",               "level": 1, "generator": "introduction",       "tables": [], "figures": []},
        {"title": "Scope",                       "level": 1, "generator": "scope",              "tables": [], "figures": []},
        {"title": "Design Standards",            "level": 1, "generator": None,                "tables": ["standards_table"], "figures": []},
        {"title": "System Overview",             "level": 1, "generator": "system_overview",   "tables": ["project_data_table"], "figures": ["speed"]},
        {"title": "Operational Parameters",      "level": 1, "generator": "operations_concept","tables": ["operational_parameters_table"], "figures": ["capacity_demand"]},
        {"title": "Rolling Stock",               "level": 1, "generator": "rolling_stock",     "tables": ["rolling_stock_table"], "figures": ["capacity_train"]},
        {"title": "Signalling & Train Control",  "level": 1, "generator": "signalling",        "tables": [], "figures": []},
        {"title": "Traction Power",              "level": 1, "generator": "traction",          "tables": [], "figures": []},
        {"title": "Telecommunications",          "level": 1, "generator": "telecom",           "tables": [], "figures": []},
        {"title": "SCADA",                       "level": 1, "generator": "scada",             "tables": [], "figures": []},
        {"title": "Platform Screen Doors",       "level": 1, "generator": "psd",               "tables": [], "figures": []},
        {"title": "RAMS Basis",                  "level": 1, "generator": "rams",              "tables": ["ram_targets_table"], "figures": ["availability"]},
        {"title": "Environmental Conditions",    "level": 1, "generator": None,                "tables": ["environmental_conditions_table"], "figures": []},
        {"title": "Conclusion",                  "level": 1, "generator": "conclusion",        "tables": [], "figures": []},
    ],

    # ───────────────────────────────────────────────
    # 4. SYSTEM REQUIREMENTS SPECIFICATION (SRS)
    # ───────────────────────────────────────────────
    "SRS": [
        {"title": "Introduction",               "level": 1, "generator": "introduction",       "tables": [], "figures": []},
        {"title": "Scope",                       "level": 1, "generator": "scope",              "tables": [], "figures": []},
        {"title": "Applicable Standards",        "level": 1, "generator": None,                "tables": ["standards_table"], "figures": []},
        {"title": "System Overview",             "level": 1, "generator": "system_overview",   "tables": ["project_data_table"], "figures": []},
        {"title": "System Requirements",         "level": 1, "generator": None,                "tables": ["srs_requirements_table"], "figures": []},
        {"title": "RAMS Requirements",           "level": 1, "generator": "rams",              "tables": ["ram_targets_table"], "figures": ["ram_pie"]},
        {"title": "Environmental Requirements",  "level": 1, "generator": None,                "tables": ["environmental_conditions_table"], "figures": []},
        {"title": "Conclusion",                  "level": 1, "generator": "conclusion",        "tables": [], "figures": []},
    ],

    # ───────────────────────────────────────────────
    # 5. RAM REPORT
    # ───────────────────────────────────────────────
    "RAM": [
        {"title": "Introduction",               "level": 1, "generator": "introduction",       "tables": [], "figures": []},
        {"title": "RAMS Methodology",            "level": 1, "generator": "rams",              "tables": [], "figures": []},
        {"title": "System Architecture",         "level": 1, "generator": "system_overview",   "tables": ["project_data_table"], "figures": []},
        {"title": "RAMS Targets",                "level": 1, "generator": None,                "tables": ["ram_targets_table"], "figures": ["availability"]},
        {"title": "Subsystem Availability Allocation","level":1,"generator": None,             "tables": ["subsystem_availability_table"], "figures": []},
        {"title": "Reliability Analysis",        "level": 1, "generator": None,                "tables": [], "figures": ["reliability"]},
        {"title": "Availability Analysis",       "level": 1, "generator": None,                "tables": [], "figures": ["ram_pie"]},
        {"title": "Maintainability Analysis",    "level": 1, "generator": "maintenance",       "tables": [], "figures": []},
        {"title": "Conclusion",                  "level": 1, "generator": "conclusion",        "tables": [], "figures": []},
    ],

    # ───────────────────────────────────────────────
    # 6. FMECA
    # ───────────────────────────────────────────────
    "FMECA": [
        {"title": "Introduction",               "level": 1, "generator": "introduction",       "tables": [], "figures": []},
        {"title": "Methodology",                 "level": 1, "generator": None,                "tables": [], "figures": []},
        {"title": "System Description",          "level": 1, "generator": "system_overview",   "tables": ["project_data_table"], "figures": []},
        {"title": "FMECA Results",               "level": 1, "generator": None,                "tables": ["fmeca_table"], "figures": []},
        {"title": "Summary and Conclusions",     "level": 1, "generator": "conclusion",        "tables": [], "figures": []},
    ],

    # ───────────────────────────────────────────────
    # 7. HAZARD LOG
    # ───────────────────────────────────────────────
    "HazardLog": [
        {"title": "Introduction",               "level": 1, "generator": "introduction",       "tables": [], "figures": []},
        {"title": "Risk Assessment Methodology", "level": 1, "generator": None,                "tables": [], "figures": []},
        {"title": "Hazard Register",             "level": 1, "generator": None,                "tables": ["hazard_log_table"], "figures": []},
        {"title": "Summary",                     "level": 1, "generator": "conclusion",        "tables": [], "figures": []},
    ],

    # ───────────────────────────────────────────────
    # 8. FLEET CALCULATION REPORT
    # ───────────────────────────────────────────────
    "FleetCalc": [
        {"title": "Introduction",               "level": 1, "generator": "introduction",       "tables": [], "figures": []},
        {"title": "Scope",                       "level": 1, "generator": "scope",              "tables": [], "figures": []},
        {"title": "Operational Parameters",      "level": 1, "generator": "operations_concept","tables": ["operational_parameters_table"], "figures": ["speed"]},
        {"title": "Fleet Calculation",           "level": 1, "generator": None,                "tables": ["fleet_calculation_table"], "figures": ["fleet"]},
        {"title": "Headway Analysis",            "level": 1, "generator": None,                "tables": ["headway_breakdown_table"], "figures": ["headway"]},
        {"title": "Capacity Analysis",           "level": 1, "generator": None,                "tables": [], "figures": ["capacity_demand", "capacity_train"]},
        {"title": "Conclusion",                  "level": 1, "generator": "conclusion",        "tables": [], "figures": []},
    ],

    # ───────────────────────────────────────────────
    # 9. INTERFACE MATRIX
    # ───────────────────────────────────────────────
    "InterfaceMatrix": [
        {"title": "Introduction",               "level": 1, "generator": "introduction",       "tables": [], "figures": []},
        {"title": "Scope",                       "level": 1, "generator": "scope",              "tables": [], "figures": []},
        {"title": "Subsystem Definitions",       "level": 1, "generator": "system_overview",   "tables": ["project_data_table"], "figures": []},
        {"title": "Interface Register",          "level": 1, "generator": None,                "tables": ["interface_matrix_table"], "figures": []},
        {"title": "Conclusion",                  "level": 1, "generator": "conclusion",        "tables": [], "figures": []},
    ],

    # ───────────────────────────────────────────────
    # 10. HEADWAY STUDY
    # ───────────────────────────────────────────────
    "HeadwayStudy": [
        {"title": "Introduction",               "level": 1, "generator": "introduction",       "tables": [], "figures": []},
        {"title": "Methodology",                 "level": 1, "generator": "signalling",        "tables": [], "figures": []},
        {"title": "Headway Calculation",         "level": 1, "generator": None,                "tables": ["headway_breakdown_table"], "figures": ["headway"]},
        {"title": "Fleet Sizing",                "level": 1, "generator": None,                "tables": ["fleet_calculation_table"], "figures": ["fleet", "train_diagram"]},
        {"title": "Conclusion",                  "level": 1, "generator": "conclusion",        "tables": [], "figures": []},
    ],

    # ───────────────────────────────────────────────
    # 11. CAPACITY STUDY
    # ───────────────────────────────────────────────
    "CapacityStudy": [
        {"title": "Introduction",               "level": 1, "generator": "introduction",       "tables": [], "figures": []},
        {"title": "Demand Analysis",             "level": 1, "generator": "operations_concept","tables": ["operational_parameters_table"], "figures": []},
        {"title": "Train Capacity",              "level": 1, "generator": "rolling_stock",     "tables": ["rolling_stock_table"], "figures": ["capacity_train"]},
        {"title": "Line Capacity",               "level": 1, "generator": None,                "tables": ["headway_breakdown_table"], "figures": ["capacity_demand"]},
        {"title": "Conclusion",                  "level": 1, "generator": "conclusion",        "tables": [], "figures": []},
    ],

    # ───────────────────────────────────────────────
    # 12. EXECUTIVE SUMMARY
    # ───────────────────────────────────────────────
    "ExecutiveSummary": [
        {"title": "Project Overview",            "level": 1, "generator": "system_overview",   "tables": ["project_data_table"], "figures": ["speed"]},
        {"title": "Operational Summary",         "level": 1, "generator": "operations_concept","tables": ["operational_parameters_table"], "figures": ["capacity_demand"]},
        {"title": "Fleet Summary",               "level": 1, "generator": None,                "tables": ["fleet_calculation_table"], "figures": ["fleet"]},
        {"title": "RAMS Summary",                "level": 1, "generator": "rams",              "tables": ["ram_targets_table"], "figures": ["availability"]},
        {"title": "Conclusion",                  "level": 1, "generator": "conclusion",        "tables": [], "figures": []},
    ],

    # ───────────────────────────────────────────────
    # 13. SIGNALLING DESCRIPTION
    # ───────────────────────────────────────────────
    "SignallingDesc": [
        {"title": "Introduction",               "level": 1, "generator": "introduction",       "tables": [], "figures": []},
        {"title": "System Overview",             "level": 1, "generator": "signalling",        "tables": ["project_data_table"], "figures": []},
        {"title": "Headway Analysis",            "level": 1, "generator": None,                "tables": ["headway_breakdown_table"], "figures": ["headway"]},
        {"title": "RAMS",                        "level": 1, "generator": "rams",              "tables": ["ram_targets_table"], "figures": []},
        {"title": "Conclusion",                  "level": 1, "generator": "conclusion",        "tables": [], "figures": []},
    ],

    # ───────────────────────────────────────────────
    # 14. MAINTENANCE PLAN
    # ───────────────────────────────────────────────
    "MaintenancePlan": [
        {"title": "Introduction",               "level": 1, "generator": "introduction",       "tables": [], "figures": []},
        {"title": "Maintenance Strategy",        "level": 1, "generator": "maintenance",       "tables": [], "figures": []},
        {"title": "Subsystem Maintenance",       "level": 1, "generator": None,                "tables": ["subsystem_availability_table"], "figures": []},
        {"title": "RAMS Targets",                "level": 1, "generator": "rams",              "tables": ["ram_targets_table"], "figures": ["ram_pie"]},
        {"title": "Conclusion",                  "level": 1, "generator": "conclusion",        "tables": [], "figures": []},
    ],

    # ───────────────────────────────────────────────
    # 15. ENVIRONMENTAL CONDITIONS REPORT
    # ───────────────────────────────────────────────
    "EnvConditions": [
        {"title": "Introduction",               "level": 1, "generator": "introduction",       "tables": [], "figures": []},
        {"title": "Environmental Conditions",    "level": 1, "generator": None,                "tables": ["environmental_conditions_table"], "figures": []},
        {"title": "Equipment Qualification",     "level": 1, "generator": None,                "tables": ["standards_table"], "figures": []},
        {"title": "Conclusion",                  "level": 1, "generator": "conclusion",        "tables": [], "figures": []},
    ],
}

# Add remaining document types with minimal structure (full BOD-like)
for _key in ["POP", "SystemDesc", "TechSpec", "Reliability", "Availability",
             "Maintainability", "DepotConOps", "OCCConOps", "TractionDesc",
             "TelecomDesc", "SCADADesc", "PSDDesc", "PISDesc", "CCTVDesc",
             "PADesc", "Performance", "OperSim"]:
    if _key not in TEMPLATES:
        TEMPLATES[_key] = [
            {"title": "Introduction",            "level": 1, "generator": "introduction",       "tables": [], "figures": []},
            {"title": "Scope",                   "level": 1, "generator": "scope",              "tables": [], "figures": []},
            {"title": "System Overview",         "level": 1, "generator": "system_overview",   "tables": ["project_data_table"], "figures": []},
            {"title": "Operational Parameters",  "level": 1, "generator": "operations_concept","tables": ["operational_parameters_table"], "figures": ["speed"]},
            {"title": "Rolling Stock",           "level": 1, "generator": "rolling_stock",     "tables": ["rolling_stock_table"], "figures": []},
            {"title": "Signalling System",       "level": 1, "generator": "signalling",        "tables": [], "figures": []},
            {"title": "RAMS",                    "level": 1, "generator": "rams",              "tables": ["ram_targets_table"], "figures": ["availability"]},
            {"title": "Conclusion",              "level": 1, "generator": "conclusion",        "tables": [], "figures": []},
        ]

# ═══════════════════════════════════════════════════════════════════════════════
# SPECIALIST TEMPLATES — Phase 1.5 Six Critical Documents
# Each document has domain-specific sections, dedicated tables and figures.
# ALL engineering values derive from CalculatedState (no hardcoded numbers).
# ═══════════════════════════════════════════════════════════════════════════════

TEMPLATES["Reliability"] = [
    {"title": "1  Introduction",
     "level": 1, "generator": "introduction",
     "tables": [], "figures": []},

    {"title": "2  Scope and Applicable Standards",
     "level": 1, "generator": "scope",
     "tables": ["standards_table"], "figures": []},

    {"title": "3  System Reliability Model",
     "level": 1, "generator": "rams",
     "tables": [], "figures": []},

    {"title": "3.1  Reliability Block Diagram",
     "level": 2, "generator": None,
     "tables": ["reliability_block_diagram_table"], "figures": []},

    {"title": "3.2  MTBF Allocation per Subsystem",
     "level": 2, "generator": None,
     "tables": ["reliability_mtbf_allocation_table"], "figures": []},

    {"title": "3.3  System Parameters and Failure Rate",
     "level": 2, "generator": None,
     "tables": ["ram_targets_table"], "figures": []},

    {"title": "4  Mission Reliability R(t)",
     "level": 1, "generator": None,
     "tables": ["reliability_R_t_table"],
     "figures": ["reliability_multiline"]},

    {"title": "5  Performance KPIs",
     "level": 1, "generator": None,
     "tables": ["performance_kpi_table"], "figures": []},

    {"title": "6  Conclusion",
     "level": 1, "generator": "conclusion",
     "tables": [], "figures": []},
]

TEMPLATES["Availability"] = [
    {"title": "1  Introduction",
     "level": 1, "generator": "introduction",
     "tables": [], "figures": []},

    {"title": "2  Availability Targets and Definitions",
     "level": 1, "generator": "scope",
     "tables": [], "figures": []},

    {"title": "3  Availability Budget",
     "level": 1, "generator": None,
     "tables": ["availability_budget_table"], "figures": []},

    {"title": "4  Subsystem Availability Allocation",
     "level": 1, "generator": None,
     "tables": ["availability_subsystem_comparison_table"],
     "figures": []},

    {"title": "4.1  Series Availability Model",
     "level": 2, "generator": None,
     "tables": ["subsystem_availability_table"], "figures": []},

    {"title": "4.2  Availability Waterfall",
     "level": 2, "generator": None,
     "tables": ["availability_waterfall_table"],
     "figures": ["availability_waterfall"]},

    {"title": "5  RAM Summary Targets vs. Predicted",
     "level": 1, "generator": None,
     "tables": ["ram_targets_table"], "figures": []},

    {"title": "6  Conclusion",
     "level": 1, "generator": "conclusion",
     "tables": [], "figures": []},
]

TEMPLATES["Maintainability"] = [
    {"title": "1  Introduction",
     "level": 1, "generator": "introduction",
     "tables": [], "figures": []},

    {"title": "2  Maintainability Framework",
     "level": 1, "generator": "maintenance",
     "tables": [], "figures": []},

    {"title": "3  Maintainability Function M(t)",
     "level": 1, "generator": None,
     "tables": ["maintainability_M_t_table"],
     "figures": ["maintainability_M_t"]},

    {"title": "4  Maintenance Levels L1–L4",
     "level": 1, "generator": None,
     "tables": ["maintenance_levels_table"], "figures": []},

    {"title": "5  Corrective vs. Preventive Maintenance Balance",
     "level": 1, "generator": None,
     "tables": ["corrective_vs_preventive_table"], "figures": []},

    {"title": "6  MTTR by Subsystem and Availability Impact",
     "level": 1, "generator": None,
     "tables": ["subsystem_availability_table",
                "ram_targets_table"], "figures": []},

    {"title": "7  Performance KPIs",
     "level": 1, "generator": None,
     "tables": ["performance_kpi_table"], "figures": []},

    {"title": "8  Conclusion",
     "level": 1, "generator": "conclusion",
     "tables": [], "figures": []},
]

TEMPLATES["HazardLog"] = [
    {"title": "1  Introduction",
     "level": 1, "generator": "introduction",
     "tables": [], "figures": []},

    {"title": "2  Hazard Identification Methodology",
     "level": 1, "generator": "scope",
     "tables": ["standards_table"], "figures": []},

    {"title": "3  System Parameters Informing Hazard Severity",
     "level": 1, "generator": None,
     "tables": ["project_data_table",
                "headway_breakdown_table"], "figures": []},

    {"title": "4  Hazard Risk Matrix",
     "level": 1, "generator": None,
     "tables": [],
     "figures": ["hazard_risk_matrix"]},

    {"title": "5  Hazard Log Register",
     "level": 1, "generator": None,
     "tables": ["hazard_log_with_cs_table"], "figures": []},

    {"title": "6  FMECA Summary",
     "level": 1, "generator": None,
     "tables": ["fmeca_table"], "figures": []},

    {"title": "7  Conclusion",
     "level": 1, "generator": "conclusion",
     "tables": [], "figures": []},
]

TEMPLATES["EnergyMgmt"] = [
    {"title": "1  Introduction",
     "level": 1, "generator": "introduction",
     "tables": [], "figures": []},

    {"title": "2  Scope and Regulatory Framework",
     "level": 1, "generator": "scope",
     "tables": ["standards_table"], "figures": []},

    {"title": "3  Traction Energy Model",
     "level": 1, "generator": "traction",
     "tables": [], "figures": []},

    {"title": "3.1  Energy Component Breakdown",
     "level": 2, "generator": None,
     "tables": ["energy_balance_table"],
     "figures": ["energy_breakdown"]},

    {"title": "3.2  Annual Energy Consumption",
     "level": 2, "generator": None,
     "tables": [],
     "figures": ["energy_annual_pie"]},

    {"title": "4  Substation Sizing",
     "level": 1, "generator": None,
     "tables": ["substation_sizing_table"],
     "figures": ["availability"]},

    {"title": "5  Energy KPIs",
     "level": 1, "generator": None,
     "tables": ["energy_kpi_table",
                "traction_parameters_table"], "figures": []},

    {"title": "6  Conclusion",
     "level": 1, "generator": "conclusion",
     "tables": [], "figures": []},
]

TEMPLATES["HumanFactors"] = [
    {"title": "1  Introduction",
     "level": 1, "generator": "introduction",
     "tables": [], "figures": []},

    {"title": "2  Scope and Human Factors Standards",
     "level": 1, "generator": "scope",
     "tables": ["standards_table"], "figures": []},

    {"title": "3  Operations Concept and GoA Level",
     "level": 1, "generator": "occ",
     "tables": [], "figures": []},

    {"title": "4  OCC Operator Workload",
     "level": 1, "generator": None,
     "tables": ["occ_workload_table"],
     "figures": ["occ_workload_radar"]},

    {"title": "5  Staffing Model",
     "level": 1, "generator": None,
     "tables": ["staffing_table"], "figures": []},

    {"title": "6  Operator Responsibilities (RACI)",
     "level": 1, "generator": None,
     "tables": ["operator_responsibilities_table"], "figures": []},

    {"title": "7  Passenger Evacuation Assumptions",
     "level": 1, "generator": None,
     "tables": ["evacuation_assumptions_table"], "figures": []},

    {"title": "8  Emergency Procedures",
     "level": 1, "generator": "emergency_operation",
     "tables": ["hazard_log_table"], "figures": []},

    {"title": "9  Conclusion",
     "level": 1, "generator": "conclusion",
     "tables": [], "figures": []},
]

# Also add "EnergyMgmt" and "HumanFactors" to DOCUMENT_TYPES if not present
# (done in config.py — add mapping here for completeness)
_NEW_DOC_KEYS = ["EnergyMgmt", "HumanFactors"]

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — NINE ADDITIONAL SPECIALIST TEMPLATES
# Priority order per specification. All reference CalculatedState.
# ═══════════════════════════════════════════════════════════════════════════════

# 1. POP — Preliminary Operation Plan
TEMPLATES["POP"] = [
    {"title": "1  Introduction and Purpose",
     "level": 1, "generator": "introduction",
     "tables": [], "figures": []},
    {"title": "2  Line Description and Operating Parameters",
     "level": 1, "generator": "system_overview",
     "tables": ["project_data_table"], "figures": []},
    {"title": "3  Operational Fleet and Service Pattern",
     "level": 1, "generator": "operations_concept",
     "tables": ["fleet_calculation_table",
                "operational_parameters_table"], "figures": ["fleet"]},
    {"title": "4  Service Headway and Capacity",
     "level": 1, "generator": None,
     "tables": ["headway_breakdown_table",
                "capacity_study_table"],
     "figures": ["headway", "capacity_demand"]},
    {"title": "5  Normal Operating Procedures",
     "level": 1, "generator": "normal_operation",
     "tables": [], "figures": []},
    {"title": "6  Degraded and Emergency Operating Procedures",
     "level": 1, "generator": "degraded_operation",
     "tables": [], "figures": []},
    {"title": "7  Performance Key Indicators",
     "level": 1, "generator": None,
     "tables": ["performance_kpi_table"], "figures": []},
    {"title": "8  Applicable Standards",
     "level": 1, "generator": None,
     "tables": ["standards_table"], "figures": []},
    {"title": "9  Conclusion",
     "level": 1, "generator": "conclusion",
     "tables": [], "figures": []},
]

# 2. SystemDesc — System Description
TEMPLATES["SystemDesc"] = [
    {"title": "1  Introduction",
     "level": 1, "generator": "introduction",
     "tables": [], "figures": []},
    {"title": "2  System Overview",
     "level": 1, "generator": "system_overview",
     "tables": ["project_data_table"], "figures": []},
    {"title": "3  Alignment and Infrastructure",
     "level": 1, "generator": "alignment",
     "tables": [], "figures": ["train_diagram"]},
    {"title": "4  Rolling Stock",
     "level": 1, "generator": "rolling_stock",
     "tables": ["rolling_stock_table"],
     "figures": ["capacity_train"]},
    {"title": "5  Signalling and Train Control",
     "level": 1, "generator": "signalling",
     "tables": ["headway_breakdown_table"],
     "figures": ["headway"]},
    {"title": "6  Traction Power Supply",
     "level": 1, "generator": "traction",
     "tables": ["traction_parameters_table"], "figures": ["energy_breakdown"]},
    {"title": "7  Telecommunications",
     "level": 1, "generator": "telecom",
     "tables": [], "figures": []},
    {"title": "8  Platform Screen Doors",
     "level": 1, "generator": "psd",
     "tables": [], "figures": []},
    {"title": "9  Subsystem Interface Summary",
     "level": 1, "generator": None,
     "tables": ["interface_matrix_table"], "figures": []},
    {"title": "10  Conclusion",
     "level": 1, "generator": "conclusion",
     "tables": [], "figures": []},
]

# 3. TechSpec — Technical Specification
TEMPLATES["TechSpec"] = [
    {"title": "1  Introduction and Scope",
     "level": 1, "generator": "introduction",
     "tables": ["standards_table"], "figures": []},
    {"title": "2  Performance Requirements",
     "level": 1, "generator": None,
     "tables": ["operational_parameters_table",
                "performance_kpi_table"], "figures": ["speed"]},
    {"title": "3  Capacity Requirements",
     "level": 1, "generator": None,
     "tables": ["capacity_study_table"], "figures": ["capacity_demand"]},
    {"title": "4  RAMS Requirements",
     "level": 1, "generator": "rams",
     "tables": ["ram_targets_table",
                "subsystem_availability_table"], "figures": ["availability"]},
    {"title": "5  Traction and Energy Requirements",
     "level": 1, "generator": "traction",
     "tables": ["traction_parameters_table",
                "energy_kpi_table"], "figures": ["energy_breakdown"]},
    {"title": "6  Signalling Requirements",
     "level": 1, "generator": "signalling",
     "tables": ["headway_breakdown_table",
                "srs_requirements_table"], "figures": []},
    {"title": "7  Environmental Conditions",
     "level": 1, "generator": None,
     "tables": ["environmental_conditions_table"], "figures": []},
    {"title": "8  Verification and Validation",
     "level": 1, "generator": "scope",
     "tables": [], "figures": []},
    {"title": "9  Conclusion",
     "level": 1, "generator": "conclusion",
     "tables": [], "figures": []},
]

# 4. DepotConOps — Depot Concept of Operations
TEMPLATES["DepotConOps"] = [
    {"title": "1  Introduction",
     "level": 1, "generator": "introduction",
     "tables": [], "figures": []},
    {"title": "2  Depot Purpose and Fleet Management",
     "level": 1, "generator": "operations_concept",
     "tables": ["fleet_calculation_table"], "figures": ["fleet"]},
    {"title": "3  Stabling and Maintenance Activities",
     "level": 1, "generator": "maintenance",
     "tables": ["maintenance_levels_table"], "figures": []},
    {"title": "4  Depot Movements and Safety",
     "level": 1, "generator": "degraded_operation",
     "tables": ["hazard_log_table"], "figures": []},
    {"title": "5  Corrective vs. Preventive Maintenance Balance",
     "level": 1, "generator": None,
     "tables": ["corrective_vs_preventive_table"], "figures": []},
    {"title": "6  RAMS Requirements for Depot",
     "level": 1, "generator": None,
     "tables": ["ram_targets_table"], "figures": []},
    {"title": "7  Staffing and Responsibilities",
     "level": 1, "generator": None,
     "tables": ["staffing_table"], "figures": []},
    {"title": "8  Conclusion",
     "level": 1, "generator": "conclusion",
     "tables": [], "figures": []},
]

# 5. OCCConOps — OCC Concept of Operations
TEMPLATES["OCCConOps"] = [
    {"title": "1  Introduction",
     "level": 1, "generator": "introduction",
     "tables": [], "figures": []},
    {"title": "2  OCC Functions and Operational Authority",
     "level": 1, "generator": "occ",
     "tables": ["occ_workload_table"],
     "figures": ["occ_workload_radar"]},
    {"title": "3  Service Supervision",
     "level": 1, "generator": "normal_operation",
     "tables": ["operational_parameters_table",
                "fleet_calculation_table"], "figures": []},
    {"title": "4  SCADA and Systems Monitoring",
     "level": 1, "generator": "scada",
     "tables": [], "figures": []},
    {"title": "5  Incident and Emergency Management",
     "level": 1, "generator": "emergency_operation",
     "tables": ["hazard_log_table"], "figures": []},
    {"title": "6  Staffing and RACI",
     "level": 1, "generator": None,
     "tables": ["staffing_table",
                "operator_responsibilities_table"], "figures": []},
    {"title": "7  Communication Systems",
     "level": 1, "generator": "telecom",
     "tables": [], "figures": []},
    {"title": "8  Performance Monitoring",
     "level": 1, "generator": None,
     "tables": ["performance_kpi_table"], "figures": []},
    {"title": "9  Conclusion",
     "level": 1, "generator": "conclusion",
     "tables": [], "figures": []},
]

# 6. TractionDesc — Traction Power Description (replaces generic)
TEMPLATES["TractionDesc"] = [
    {"title": "1  Introduction",
     "level": 1, "generator": "introduction",
     "tables": [], "figures": []},
    {"title": "2  Power Supply System Overview",
     "level": 1, "generator": "traction",
     "tables": [], "figures": []},
    {"title": "3  Substation Configuration and Rating",
     "level": 1, "generator": None,
     "tables": ["substation_sizing_table"], "figures": []},
    {"title": "4  Traction Energy Model",
     "level": 1, "generator": None,
     "tables": ["energy_balance_table"],
     "figures": ["energy_breakdown", "energy_annual_pie"]},
    {"title": "5  Regenerative Braking",
     "level": 1, "generator": None,
     "tables": ["traction_parameters_table"], "figures": []},
    {"title": "6  Energy KPIs",
     "level": 1, "generator": None,
     "tables": ["energy_kpi_table"], "figures": []},
    {"title": "7  Applicable Standards",
     "level": 1, "generator": None,
     "tables": ["standards_table"], "figures": []},
    {"title": "8  Conclusion",
     "level": 1, "generator": "conclusion",
     "tables": [], "figures": []},
]

# 7. Safety Case (new key: "SafetyCase")
TEMPLATES["SafetyCase"] = [
    {"title": "1  Introduction and Safety Objectives",
     "level": 1, "generator": "introduction",
     "tables": [], "figures": []},
    {"title": "2  System Description and Operational Context",
     "level": 1, "generator": "system_overview",
     "tables": ["project_data_table"], "figures": []},
    {"title": "3  Applicable Safety Standards",
     "level": 1, "generator": "scope",
     "tables": ["standards_table"], "figures": []},
    {"title": "4  Hazard Identification and Risk Assessment",
     "level": 1, "generator": None,
     "tables": ["hazard_log_table"],
     "figures": ["hazard_risk_matrix"]},
    {"title": "5  FMECA and Failure Mode Analysis",
     "level": 1, "generator": None,
     "tables": ["fmeca_table"], "figures": []},
    {"title": "6  RAMS Demonstration",
     "level": 1, "generator": "rams",
     "tables": ["ram_targets_table",
                "subsystem_availability_table"],
     "figures": ["reliability_multiline"]},
    {"title": "7  Safety Requirement Compliance",
     "level": 1, "generator": None,
     "tables": ["srs_requirements_table"], "figures": []},
    {"title": "8  Residual Risk and Acceptance",
     "level": 1, "generator": "emergency_operation",
     "tables": [], "figures": []},
    {"title": "9  Conclusion",
     "level": 1, "generator": "conclusion",
     "tables": [], "figures": []},
]

# 8. Performance Report
TEMPLATES["Performance"] = [
    {"title": "1  Introduction",
     "level": 1, "generator": "introduction",
     "tables": [], "figures": []},
    {"title": "2  Commercial Performance",
     "level": 1, "generator": None,
     "tables": ["operational_parameters_table",
                "performance_kpi_table"],
     "figures": ["speed", "fleet"]},
    {"title": "3  Capacity Performance",
     "level": 1, "generator": None,
     "tables": ["capacity_study_table"],
     "figures": ["capacity_demand", "capacity_train"]},
    {"title": "4  RAMS Performance",
     "level": 1, "generator": "rams",
     "tables": ["ram_targets_table",
                "reliability_mtbf_allocation_table"],
     "figures": ["reliability_multiline", "availability_waterfall"]},
    {"title": "5  Energy Performance",
     "level": 1, "generator": None,
     "tables": ["energy_kpi_table",
                "energy_balance_table"],
     "figures": ["energy_breakdown"]},
    {"title": "6  Conclusion",
     "level": 1, "generator": "conclusion",
     "tables": [], "figures": []},
]

# 9. Operational Simulation Report
TEMPLATES["OperSim"] = [
    {"title": "1  Introduction and Simulation Scope",
     "level": 1, "generator": "introduction",
     "tables": [], "figures": []},
    {"title": "2  Simulation Inputs — Verified CalculatedState",
     "level": 1, "generator": None,
     "tables": ["project_data_table",
                "operational_parameters_table"], "figures": []},
    {"title": "3  Headway and Separation Analysis",
     "level": 1, "generator": None,
     "tables": ["headway_breakdown_table"],
     "figures": ["headway", "train_diagram"]},
    {"title": "4  Fleet and Capacity Results",
     "level": 1, "generator": None,
     "tables": ["fleet_calculation_table",
                "capacity_study_table"],
     "figures": ["fleet", "capacity_demand"]},
    {"title": "5  RAMS Simulation Results",
     "level": 1, "generator": None,
     "tables": ["reliability_R_t_table",
                "reliability_mtbf_allocation_table"],
     "figures": ["reliability_multiline"]},
    {"title": "6  Energy Simulation Results",
     "level": 1, "generator": None,
     "tables": ["energy_balance_table",
                "energy_kpi_table"],
     "figures": ["energy_annual_pie"]},
    {"title": "7  Key Performance Indicators",
     "level": 1, "generator": None,
     "tables": ["performance_kpi_table"], "figures": []},
    {"title": "8  Conclusions and Recommendations",
     "level": 1, "generator": "conclusion",
     "tables": [], "figures": []},
]

# Register SafetyCase in the template registry
# (SafetyCase key not in DOCUMENT_TYPES yet — handled in config.py)
