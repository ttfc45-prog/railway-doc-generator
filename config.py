"""
config.py
Railway Documentation Generator — Application Constants
========================================================

Contains ONLY:
  • Path constants
  • AI provider settings
  • Document catalogue
  • Subsystem catalogue
  • Risk matrices
  • Word/figure styling constants
  • UI tab labels

DEFAULT_PROJECT is now an ALIAS to project_model.DEFAULT_INPUTS.
It contains ONLY primitive user inputs — no calculated outputs.

Any module that previously used config.DEFAULT_PROJECT directly
now gets the same clean dict via this alias.
"""

from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PATH CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

import os as _os

BASE_DIR      = Path(__file__).resolve().parent

# On Streamlit Cloud the app directory is read-only.
# Use /tmp for all generated outputs when the local output/ dir is not writable.
def _writable(p: Path) -> bool:
    try:
        p.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False

_local_out = BASE_DIR / "output"
if _writable(_local_out):
    OUTPUT_DIR = _local_out
else:
    OUTPUT_DIR = Path("/tmp/rdg_output")

OUTPUT_DOCX   = OUTPUT_DIR / "docx"
OUTPUT_PDF    = OUTPUT_DIR / "pdf"
OUTPUT_EXCEL  = OUTPUT_DIR / "excel"
OUTPUT_FIGS   = OUTPUT_DIR / "figures"
OUTPUT_TABS   = OUTPUT_DIR / "tables"
DATA_DIR      = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"

for _d in [OUTPUT_DOCX, OUTPUT_PDF, OUTPUT_EXCEL, OUTPUT_FIGS, OUTPUT_TABS]:
    _d.mkdir(parents=True, exist_ok=True)

for _d in [DATA_DIR / "stations", DATA_DIR / "rolling_stock",
           DATA_DIR / "headway",  DATA_DIR / "traction_power", DATA_DIR / "rams"]:
    try:
        _d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────────────────────
# AI PROVIDER CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

AI_PROVIDER      = "anthropic"
ANTHROPIC_MODEL  = "claude-sonnet-4-6"
OPENAI_MODEL     = "gpt-4o"
MAX_TOKENS       = 2048
AI_TEMPERATURE   = 0.3          # low = professional / reproducible

# ─────────────────────────────────────────────────────────────────────────────
# DEFAULT PROJECT — alias to project_model.DEFAULT_INPUTS
# All modules that import DEFAULT_PROJECT now receive a dict that contains
# ONLY primitive user inputs.  No calculated values.
# ─────────────────────────────────────────────────────────────────────────────

from project_model import DEFAULT_INPUTS as DEFAULT_PROJECT   # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT CATALOGUE (32 types)
# ─────────────────────────────────────────────────────────────────────────────

DOCUMENT_TYPES = {
    "ConOps":           "Concept of Operations",
    "OCS":              "Operation Control Strategy",
    "POP":              "Preliminary Operation Plan",
    "BOD":              "Basis of Design",
    "SystemDesc":       "System Description",
    "SRS":              "System Requirements Specification",
    "TechSpec":         "Technical Specification",
    "InterfaceMatrix":  "Interface Matrix",
    "RAM":              "RAM Report",
    "Reliability":      "Reliability Report",
    "Availability":     "Availability Report",
    "Maintainability":  "Maintainability Report",
    "FMECA":            "FMECA Report",
    "HazardLog":        "Hazard Log",
    "MaintenancePlan":  "Maintenance Plan",
    "DepotConOps":      "Depot Operation Concept",
    "OCCConOps":        "OCC Operation Concept",
    "SignallingDesc":   "Signalling System Description",
    "TractionDesc":     "Traction Power Description",
    "TelecomDesc":      "Telecommunications Description",
    "SCADADesc":        "SCADA System Description",
    "PSDDesc":          "Platform Screen Door Description",
    "PISDesc":          "Passenger Information System Description",
    "CCTVDesc":         "CCTV System Description",
    "PADesc":           "Public Address System Description",
    "EnvConditions":    "Environmental Conditions Report",
    "Performance":      "Performance Report",
    "OperSim":          "Operational Simulation Report",
    "HeadwayStudy":     "Headway Study",
    "FleetCalc":        "Fleet Calculation Report",
    "CapacityStudy":    "Capacity Study",
    "ExecutiveSummary": "Executive Summary",
    "EnergyMgmt":       "Energy Management Plan",
    "HumanFactors":     "Human Factors Report",
    "SafetyCase":       "Safety Case",
}

# ─────────────────────────────────────────────────────────────────────────────
# SUBSYSTEM CATALOGUE
# ─────────────────────────────────────────────────────────────────────────────

SUBSYSTEMS = [
    "Track & Civil Works",
    "Rolling Stock",
    "Signalling (CBTC/ATP/ATO/ATS/Interlocking)",
    "Telecommunications",
    "SCADA",
    "Platform Screen Doors (PSD)",
    "Operations Control Centre (OCC)",
    "Traction Power Supply",
    "Depot Equipment",
    "CCTV System",
    "Public Address (PA) System",
    "Passenger Information System (PIS)",
    "Automatic Fare Collection (AFC)",
    "Fire Detection & Suppression",
    "Ventilation & HVAC",
]

# ─────────────────────────────────────────────────────────────────────────────
# SEVERITY / PROBABILITY / RISK MATRICES (EN 50126-1)
# ─────────────────────────────────────────────────────────────────────────────

SEVERITY_LEVELS = {
    1: ("Negligible",   "No injury or minor property damage"),
    2: ("Marginal",     "Minor injury or significant property damage"),
    3: ("Critical",     "Severe injury or major property damage"),
    4: ("Catastrophic", "Multiple fatalities or loss of system"),
}

PROBABILITY_LEVELS = {
    1: ("Improbable",  "< 1×10⁻⁹ per hour"),
    2: ("Remote",      "1×10⁻⁹ to 1×10⁻⁷ per hour"),
    3: ("Occasional",  "1×10⁻⁷ to 1×10⁻⁵ per hour"),
    4: ("Probable",    "1×10⁻⁵ to 1×10⁻³ per hour"),
    5: ("Frequent",    "> 1×10⁻³ per hour"),
}

RISK_MATRIX = {
    (1,1):"Acceptable",  (1,2):"Acceptable",  (1,3):"Acceptable",
    (1,4):"Undesirable", (1,5):"Undesirable",
    (2,1):"Acceptable",  (2,2):"Acceptable",  (2,3):"Undesirable",
    (2,4):"Undesirable", (2,5):"Intolerable",
    (3,1):"Acceptable",  (3,2):"Undesirable", (3,3):"Intolerable",
    (3,4):"Intolerable", (3,5):"Intolerable",
    (4,1):"Undesirable", (4,2):"Intolerable", (4,3):"Intolerable",
    (4,4):"Intolerable", (4,5):"Intolerable",
}

# ─────────────────────────────────────────────────────────────────────────────
# WORD DOCUMENT STYLES
# ─────────────────────────────────────────────────────────────────────────────

FONT_NAME         = "Arial"
FONT_SIZE_BODY    = 10
FONT_SIZE_H1      = 16
FONT_SIZE_H2      = 13
FONT_SIZE_H3      = 11
FONT_SIZE_CAPTION = 9
PAGE_MARGIN_CM    = 2.54
HEADER_COLOR      = "003087"     # dark blue (SYSTRA / consulting standard)
ACCENT_COLOR      = "E8352B"     # red accent
TABLE_HEADER_BG   = "003087"
TABLE_ALT_BG      = "EAF0FB"

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

FIGURE_DPI        = 150
FIGURE_WIDTH_IN   = 10
FIGURE_HEIGHT_IN  = 5
PLOT_STYLE        = "seaborn-v0_8-whitegrid"
PALETTE           = ["#003087", "#E8352B", "#F4A300", "#28A745", "#6C757D", "#17A2B8"]

# ─────────────────────────────────────────────────────────────────────────────
# UI TAB LABELS
# ─────────────────────────────────────────────────────────────────────────────

UI_TABS = [
    "🏗️ Project",
    "🛤️ Infrastructure",
    "🚆 Operations",
    "🚃 Rolling Stock",
    "🚦 Signalling",
    "⚡ Traction Power",
    "🏭 Depot",
    "📡 Telecommunications",
    "🚪 Platform Screen Doors",
    "🖥️ SCADA",
    "📊 RAMS",
    "🔧 Maintenance",
    "🌡️ Environmental",
    "📄 Export",
    "🔍 Audit",
    "🕸️ Dependency",
    "🔄 Impact",
]
