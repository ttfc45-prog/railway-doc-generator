"""
dependency_graph.py
Railway Documentation Generator — Parameter Dependency Graph
============================================================

Generates the complete parameter dependency graph for the CalculationEngine pipeline.

Architecture represented:
  ProjectModel.inputs
      ↓
  [headway calculation]   ← max_speed, emergency_deceleration
      ↓
  [operations calculation] ← headway_sec, line_length, n_stations, acceleration, dwell
      ↓
  [capacity calculation]  ← ops.headway_sec, seated_capacity, standing_capacity
      ↓
  [ram calculation]       ← mtbf_target, mttr_target, ops.commercial_speed
      ↓
  [traction calculation]  ← ops.commercial_speed, ops.annual_train_km, ops.fleet_required
      ↓
  [rams_allocation]       ← ram.mtbf_hours, complexity_weights
      ↓
  Documents (each reads from specific CalculatedState fields)

Outputs:
  • Mermaid (.mmd) — rendered in GitHub, Notion, documentation platforms
  • SVG — self-contained vector graphic for Word/PDF embedding
  • JSON — machine-readable graph for tooling
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ═══════════════════════════════════════════════════════════════════════════════
# GRAPH STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GraphNode:
    id:       str        # unique identifier, no spaces
    label:    str        # human-readable display label
    category: str        # "input" | "calculated" | "document" | "function"
    layer:    int        # 0=inputs, 1=headway, 2=ops, 3=capacity/ram/traction, 4=allocation, 5=docs
    value:    str = ""   # current value (filled at runtime)
    unit:     str = ""


@dataclass
class GraphEdge:
    source:  str         # node id
    target:  str         # node id
    label:   str = ""    # e.g. "provides commercial_speed"
    style:   str = "solid"  # "solid" | "dashed"


# ═══════════════════════════════════════════════════════════════════════════════
# STATIC GRAPH DEFINITION
# ═══════════════════════════════════════════════════════════════════════════════

def build_graph() -> tuple[list[GraphNode], list[GraphEdge]]:
    """
    Build the complete dependency graph.
    Nodes and edges are defined structurally — values populated separately.
    """
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    # ── Layer 0: ProjectModel Inputs ─────────────────────────────────────────
    inputs = [
        ("IN_vmax",    "Max Speed\nv_max",        "km/h",  0),
        ("IN_demg",    "Emergency\nDeceleration",  "m/s²",  0),
        ("IN_L",       "Line Length\nL",           "km",    0),
        ("IN_nstat",   "Number of\nStations",      "–",     0),
        ("IN_acc",     "Acceleration\na",          "m/s²",  0),
        ("IN_dwell",   "Station\nDwell Time",      "s",     0),
        ("IN_headway", "Service\nHeadway H",       "s",     0),
        ("IN_term",    "Terminal\nDwell",          "min",   0),
        ("IN_avail",   "Operational\nAvailability","–",     0),
        ("IN_reserv",  "Reserve\nFleet %",         "%",     0),
        ("IN_ophrs",   "Operating\nHours",         "h/day", 0),
        ("IN_seated",  "Seated\nCapacity",         "pax",   0),
        ("IN_stand6",  "Standing 6pm²\nCapacity",  "pax",   0),
        ("IN_demand",  "Peak Demand\nPPHPD",       "pphpd", 0),
        ("IN_mtbf",    "MTBF Target",              "h",     0),
        ("IN_mttr",    "MTTR Target",              "h",     0),
        ("IN_nsubs",   "N Substations",            "–",     0),
        ("IN_regen_f", "Regen Fraction",           "–",     0),
        ("IN_regen_e", "Regen Efficiency",         "–",     0),
        ("IN_aux",     "Aux. Power\n/car",         "kW",    0),
        ("IN_mass",    "Mass /car\n(AW3)",         "t",     0),
        ("IN_cars",    "Cars /train",              "–",     0),
    ]
    for nid, label, unit, layer in inputs:
        nodes.append(GraphNode(nid, label, "input", layer, unit=unit))

    # ── Layer 1: Headway Function ─────────────────────────────────────────────
    nodes.append(GraphNode("FN_hdw",  "calculate_headway()",      "function", 1))
    nodes.append(GraphNode("CS_Htech","Technical\nHeadway H_tech","calculated",1, unit="s"))
    nodes.append(GraphNode("CS_Hcomm","Commercial\nHeadway H_comm","calculated",1, unit="s"))
    nodes.append(GraphNode("CS_dsep", "Min Safe\nSeparation d_sep","calculated",1,unit="m"))
    nodes.append(GraphNode("CS_dbrk", "Braking\nDistance d_brk",  "calculated",1,unit="m"))

    edges += [
        GraphEdge("IN_vmax",  "FN_hdw", "v_max → braking time"),
        GraphEdge("IN_demg",  "FN_hdw", "d_emg → t_brk"),
        GraphEdge("IN_dwell", "FN_hdw", "t_dwell → H_comm"),
        GraphEdge("FN_hdw",   "CS_Htech"),
        GraphEdge("FN_hdw",   "CS_Hcomm"),
        GraphEdge("FN_hdw",   "CS_dsep"),
        GraphEdge("FN_hdw",   "CS_dbrk"),
    ]

    # ── Layer 2: Operations Function ──────────────────────────────────────────
    nodes.append(GraphNode("FN_ops",   "calculate_operations()",   "function",  2))
    nodes.append(GraphNode("CS_vc",    "Commercial\nSpeed v_c",    "calculated",2, unit="km/h"))
    nodes.append(GraphNode("CS_RTT",   "Round Trip\nTime RTT",     "calculated",2, unit="min"))
    nodes.append(GraphNode("CS_Nsvc",  "Trains in\nService N_s",   "calculated",2))
    nodes.append(GraphNode("CS_Nflt",  "Operational\nFleet N_flt", "calculated",2))
    nodes.append(GraphNode("CS_Nres",  "Reserve\nTrains N_res",    "calculated",2))
    nodes.append(GraphNode("CS_Ntot",  "Total\nFleet N_tot",       "calculated",2))
    nodes.append(GraphNode("CS_dkm",   "Daily\nTrain-km",          "calculated",2))
    nodes.append(GraphNode("CS_akm",   "Annual\nTrain-km",         "calculated",2))

    edges += [
        GraphEdge("IN_L",       "FN_ops"),
        GraphEdge("IN_nstat",   "FN_ops"),
        GraphEdge("IN_vmax",    "FN_ops", "v_max → kinematics"),
        GraphEdge("IN_acc",     "FN_ops"),
        GraphEdge("IN_dwell",   "FN_ops"),
        GraphEdge("IN_headway", "FN_ops", "H_service → N_s"),
        GraphEdge("IN_term",    "FN_ops"),
        GraphEdge("IN_avail",   "FN_ops"),
        GraphEdge("IN_reserv",  "FN_ops"),
        GraphEdge("IN_ophrs",   "FN_ops"),
        GraphEdge("FN_ops", "CS_vc"),
        GraphEdge("FN_ops", "CS_RTT"),
        GraphEdge("FN_ops", "CS_Nsvc"),
        GraphEdge("FN_ops", "CS_Nflt"),
        GraphEdge("FN_ops", "CS_Nres"),
        GraphEdge("FN_ops", "CS_Ntot"),
        GraphEdge("FN_ops", "CS_dkm"),
        GraphEdge("FN_ops", "CS_akm"),
    ]

    # ── Layer 3a: Capacity Function ───────────────────────────────────────────
    nodes.append(GraphNode("FN_cap",    "calculate_capacity()",    "function",  3))
    nodes.append(GraphNode("CS_cap6",   "Train Cap.\n(6 pax/m²)",  "calculated",3, unit="pax"))
    nodes.append(GraphNode("CS_pphpd6", "PPHPD\n(6 pax/m²)",      "calculated",3, unit="pphpd"))
    nodes.append(GraphNode("CS_lf6",    "Load Factor\nLF_6",       "calculated",3, unit="%"))

    edges += [
        GraphEdge("IN_seated",  "FN_cap"),
        GraphEdge("IN_stand6",  "FN_cap"),
        GraphEdge("IN_demand",  "FN_cap"),
        GraphEdge("CS_Nsvc",    "FN_cap", "headway_sec"),
        GraphEdge("FN_cap", "CS_cap6"),
        GraphEdge("FN_cap", "CS_pphpd6"),
        GraphEdge("FN_cap", "CS_lf6"),
    ]

    # ── Layer 3b: RAM Function ────────────────────────────────────────────────
    nodes.append(GraphNode("FN_ram",    "calculate_ram()",          "function",  3))
    nodes.append(GraphNode("CS_A",      "Availability\nA",          "calculated",3, unit="%"))
    nodes.append(GraphNode("CS_R24",    "Mission\nReliability R(24h)","calculated",3))
    nodes.append(GraphNode("CS_M8",     "Maintainability\nM(8h)",   "calculated",3))
    nodes.append(GraphNode("CS_MKBF",   "km Between\nFailures",     "calculated",3, unit="km"))

    edges += [
        GraphEdge("IN_mtbf", "FN_ram"),
        GraphEdge("IN_mttr", "FN_ram"),
        GraphEdge("CS_vc",   "FN_ram", "v_c → MKBF  ← correct chain"),
        GraphEdge("FN_ram", "CS_A"),
        GraphEdge("FN_ram", "CS_R24"),
        GraphEdge("FN_ram", "CS_M8"),
        GraphEdge("FN_ram", "CS_MKBF"),
    ]

    # ── Layer 3c: Traction Function ───────────────────────────────────────────
    nodes.append(GraphNode("FN_trc",    "calculate_traction()",     "function",  3))
    nodes.append(GraphNode("CS_Ppk",    "Peak Power\nP_peak",       "calculated",3, unit="kW"))
    nodes.append(GraphNode("CS_Enet",   "Net Energy\n/train-km",    "calculated",3, unit="kWh/km"))
    nodes.append(GraphNode("CS_regen",  "Regen\nSaving",            "calculated",3, unit="%"))
    nodes.append(GraphNode("CS_Subs",   "Substation\nRating",       "calculated",3, unit="MVA"))
    nodes.append(GraphNode("CS_Eyr",    "Annual\nEnergy",           "calculated",3, unit="MWh"))

    edges += [
        GraphEdge("IN_mass",    "FN_trc"),
        GraphEdge("IN_cars",    "FN_trc"),
        GraphEdge("IN_vmax",    "FN_trc", "v_max → peak power"),
        GraphEdge("IN_acc",     "FN_trc"),
        GraphEdge("IN_nsubs",   "FN_trc"),
        GraphEdge("IN_regen_f", "FN_trc"),
        GraphEdge("IN_regen_e", "FN_trc"),
        GraphEdge("IN_aux",     "FN_trc"),
        GraphEdge("CS_vc",      "FN_trc", "v_c → E_aux, E_yr"),
        GraphEdge("CS_Nflt",    "FN_trc", "fleet → subs sizing"),
        GraphEdge("CS_akm",     "FN_trc", "annual_km → E_yr  ← correct chain"),
        GraphEdge("FN_trc", "CS_Ppk"),
        GraphEdge("FN_trc", "CS_Enet"),
        GraphEdge("FN_trc", "CS_regen"),
        GraphEdge("FN_trc", "CS_Subs"),
        GraphEdge("FN_trc", "CS_Eyr"),
    ]

    # ── Layer 4: RAMS Allocation ──────────────────────────────────────────────
    nodes.append(GraphNode("FN_alloc",  "calculate_rams_allocation()","function", 4))
    nodes.append(GraphNode("CS_MTBFi",  "Subsystem\nMTBF_i",         "calculated",4, unit="h"))
    nodes.append(GraphNode("CS_Ai",     "Subsystem\nA_i",            "calculated",4, unit="%"))
    nodes.append(GraphNode("CS_Aseries","Series\nAvailability",       "calculated",4, unit="%"))
    nodes.append(GraphNode("CS_MTBFs",  "Series\nMTBF",              "calculated",4, unit="h"))

    edges += [
        GraphEdge("CS_A",    "FN_alloc", "system A → allocate"),
        GraphEdge("IN_mtbf", "FN_alloc", "MTBF → partition by weights"),
        GraphEdge("FN_alloc","CS_MTBFi"),
        GraphEdge("FN_alloc","CS_Ai"),
        GraphEdge("FN_alloc","CS_Aseries"),
        GraphEdge("FN_alloc","CS_MTBFs"),
    ]

    # ── Layer 5: Document Consumers ──────────────────────────────────────────
    doc_consumers = [
        ("DOC_conops",   "ConOps",        ["CS_vc","CS_RTT","CS_Nsvc","CS_pphpd6","CS_Htech"]),
        ("DOC_srs",      "SRS",           ["CS_vc","CS_Htech","CS_Nflt","CS_pphpd6","CS_A"]),
        ("DOC_fleet",    "Fleet Calc.",   ["CS_vc","CS_RTT","CS_Nsvc","CS_Nflt","CS_Ntot"]),
        ("DOC_headway",  "Headway Study", ["CS_Htech","CS_Hcomm","CS_dsep","CS_dbrk"]),
        ("DOC_capacity", "Capacity Study",["CS_pphpd6","CS_cap6","CS_lf6"]),
        ("DOC_ram",      "RAM Report",    ["CS_A","CS_R24","CS_M8","CS_MKBF","CS_MTBFi"]),
        ("DOC_traction", "Traction Desc.", ["CS_Ppk","CS_Enet","CS_regen","CS_Subs","CS_Eyr"]),
        ("DOC_hazard",   "Hazard Log",    ["CS_vc","CS_Htech","CS_dsep","CS_pphpd6","CS_Ntot"]),
        ("DOC_energy",   "Energy Plan",   ["CS_Enet","CS_regen","CS_Eyr","CS_Subs"]),
        ("DOC_hf",       "Human Factors", ["CS_Nsvc","CS_Ntot","CS_pphpd6","CS_cap6"]),
        ("DOC_perf",     "Performance",   ["CS_vc","CS_pphpd6","CS_A","CS_Eyr"]),
        ("DOC_safety",   "Safety Case",   ["CS_Htech","CS_dsep","CS_A","CS_MTBFi"]),
    ]
    for nid, label, sources in doc_consumers:
        nodes.append(GraphNode(nid, label, "document", 5))
        for src in sources:
            edges.append(GraphEdge(src, nid, style="dashed"))

    return nodes, edges


# ═══════════════════════════════════════════════════════════════════════════════
# VALUE POPULATION
# ═══════════════════════════════════════════════════════════════════════════════

def populate_graph_values(nodes: list[GraphNode], model, cs) -> list[GraphNode]:
    """Fill .value fields from ProjectModel inputs and CalculatedState."""
    p = model.to_dict()
    value_map = {
        "IN_vmax":    str(p.get("max_speed_kmh",80)),
        "IN_demg":    str(p.get("emergency_deceleration_mss",1.3)),
        "IN_L":       str(p.get("line_length_km",22.5)),
        "IN_nstat":   str(p.get("number_of_stations",18)),
        "IN_acc":     str(p.get("max_acceleration_mss",1.0)),
        "IN_dwell":   str(p.get("station_dwell_sec",35)),
        "IN_headway": str(p.get("peak_headway_sec",90)),
        "IN_term":    str(p.get("terminal_dwell_min",3.0)),
        "IN_avail":   str(p.get("operational_availability_target_pct",98.0)),
        "IN_reserv":  str(p.get("reserve_fleet_pct",10.0)),
        "IN_ophrs":   str(p.get("operating_hours_per_day",18)),
        "IN_seated":  str(p.get("seated_capacity",306)),
        "IN_stand6":  str(p.get("standing_capacity_6ppm2",918)),
        "IN_demand":  f"{p.get('peak_demand_pphpd',45000):,}",
        "IN_mtbf":    f"{p.get('mtbf_target_hours',50000):,}",
        "IN_mttr":    str(p.get("mttr_target_hours",4.0)),
        "IN_nsubs":   str(p.get("number_of_substations",10)),
        "IN_regen_f": str(p.get("regen_recoverable_fraction",0.30)),
        "IN_regen_e": str(p.get("regen_recovery_efficiency",0.70)),
        "IN_aux":     str(p.get("auxiliary_power_kw_per_car",15.0)),
        "IN_mass":    str(p.get("mass_per_car_tonnes",40.0)),
        "IN_cars":    str(p.get("cars_per_train",6)),
        "CS_Htech":   f"{cs.headway.technical_headway_sec:.1f}",
        "CS_Hcomm":   f"{cs.headway.commercial_headway_sec:.1f}",
        "CS_dsep":    f"{cs.headway.minimum_safe_separation_m:.0f}",
        "CS_dbrk":    f"{cs.headway.braking_distance_m:.0f}",
        "CS_vc":      f"{cs.ops.commercial_speed_kmh:.1f}",
        "CS_RTT":     f"{cs.ops.round_trip_time_min:.1f}",
        "CS_Nsvc":    str(cs.ops.trains_in_service),
        "CS_Nflt":    str(cs.ops.fleet_required),
        "CS_Nres":    str(cs.ops.reserve_trains),
        "CS_Ntot":    str(cs.ops.total_fleet),
        "CS_dkm":     f"{cs.ops.daily_train_km:,.0f}",
        "CS_akm":     f"{cs.ops.annual_train_km:,.0f}",
        "CS_cap6":    str(cs.capacity.capacity_6ppm2),
        "CS_pphpd6":  f"{cs.capacity.pphpd_6ppm2:,}",
        "CS_lf6":     f"{cs.capacity.load_factor_6ppm2_pct:.1f}",
        "CS_A":       f"{cs.ram.availability*100:.4f}",
        "CS_R24":     f"{cs.ram.mission_reliability_24h:.5f}",
        "CS_M8":      f"{cs.ram.maintainability_8h:.4f}",
        "CS_MKBF":    f"{cs.ram.km_between_failures:,.0f}",
        "CS_Ppk":     f"{cs.traction.peak_power_kw:,.0f}",
        "CS_Enet":    f"{cs.traction.energy_per_train_km_kwh:.3f}",
        "CS_regen":   f"{cs.traction.regenerative_saving_pct:.1f}",
        "CS_Subs":    f"{cs.traction.substation_rating_mva:.1f}",
        "CS_Eyr":     f"{cs.traction.annual_energy_mwh:,.0f}",
        "CS_MTBFi":   "7 subsystems allocated",
        "CS_Ai":      f"{cs.rams_alloc.series_avail_pct:.4f}",
        "CS_Aseries": f"{cs.rams_alloc.series_avail_pct:.4f}",
        "CS_MTBFs":   f"{cs.rams_alloc.series_mtbf_hours:,.0f}",
    }
    result = []
    for n in nodes:
        import copy
        node = copy.copy(n)
        if n.id in value_map:
            node.value = value_map[n.id]
        result.append(node)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# MERMAID RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_mermaid(nodes: list[GraphNode], edges: list[GraphEdge]) -> str:
    """Render dependency graph as a Mermaid flowchart (top-down)."""
    STYLES = {
        "input":      "fill:#EAF0FB,stroke:#003087,color:#003087",
        "calculated": "fill:#D5F5E3,stroke:#155724,color:#155724",
        "function":   "fill:#FEF9E7,stroke:#B7950B,color:#856404",
        "document":   "fill:#FDECEA,stroke:#C0392B,color:#7B241C",
    }

    lines = ["flowchart TD"]
    lines.append("")

    # Group by layer
    layers = {}
    for n in nodes:
        layers.setdefault(n.layer, []).append(n)

    layer_labels = {0:"Inputs",1:"Headway",2:"Operations",
                    3:"Capacity / RAM / Traction",4:"RAMS Allocation",5:"Documents"}

    for layer_idx in sorted(layers.keys()):
        layer_nodes = layers[layer_idx]
        lines.append(f"    subgraph L{layer_idx}[\"{layer_labels.get(layer_idx,'Layer '+str(layer_idx))}\"]")
        for n in layer_nodes:
            label = n.label.replace('\n','<br/>')
            if n.value:
                label += f"<br/><b>{n.value} {n.unit}</b>"
            lines.append(f"        {n.id}[\"{label}\"]")
        lines.append("    end")
        lines.append("")

    # Edges
    lines.append("    %% Dependencies")
    for e in edges:
        arrow = "-->" if e.style == "solid" else "-.->"
        if e.label:
            lines.append(f"    {e.source} {arrow}|\"{e.label}\"| {e.target}")
        else:
            lines.append(f"    {e.source} {arrow} {e.target}")

    lines.append("")
    lines.append("    %% Styles")
    for n in nodes:
        style = STYLES.get(n.category, "")
        if style:
            lines.append(f"    style {n.id} {style}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# SVG RENDERER (self-contained, no external dependencies)
# ═══════════════════════════════════════════════════════════════════════════════

def render_svg(nodes: list[GraphNode], edges: list[GraphEdge]) -> str:
    """
    Render dependency graph as a layered SVG.
    Nodes arranged in horizontal layers (top = inputs, bottom = documents).
    """
    # Layout constants
    NODE_W, NODE_H = 110, 55
    LAYER_GAP      = 100
    NODE_GAP       = 20
    MARGIN         = 60
    LAYER_LABELS   = {0:"Inputs",1:"Headway",2:"Operations",
                      3:"Cap / RAM / Traction",4:"RAMS Alloc.",5:"Documents"}

    FILL = {"input":"#EAF0FB","calculated":"#D5F5E3",
            "function":"#FEF9E7","document":"#FDECEA"}
    STROKE={"input":"#003087","calculated":"#155724",
            "function":"#B7950B","document":"#C0392B"}

    # Group nodes by layer
    layers: dict[int,list[GraphNode]] = {}
    for n in nodes:
        layers.setdefault(n.layer, []).append(n)

    # Compute positions
    positions: dict[str,tuple[float,float]] = {}
    max_layer = max(layers.keys())
    total_h   = MARGIN + (max_layer+1)*(NODE_H+LAYER_GAP) + MARGIN
    max_width = 0

    for layer_idx in sorted(layers.keys()):
        layer_nodes = layers[layer_idx]
        n_nodes     = len(layer_nodes)
        total_w     = n_nodes*(NODE_W+NODE_GAP) - NODE_GAP
        max_width   = max(max_width, total_w)
        y = MARGIN + layer_idx*(NODE_H+LAYER_GAP)
        for i, node in enumerate(layer_nodes):
            x = MARGIN + i*(NODE_W+NODE_GAP)
            positions[node.id] = (x + NODE_W/2, y + NODE_H/2)

    svg_w = max_width + 2*MARGIN
    svg_h = total_h

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" '
        f'viewBox="0 0 {svg_w} {svg_h}" font-family="Arial,sans-serif">',
        '<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" '
        'orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#888"/></marker>'
        '<marker id="arr2" markerWidth="8" markerHeight="8" refX="6" refY="3" '
        'orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#C0392B"/></marker>'
        '</defs>',
    ]

    # Layer background bands
    for layer_idx in sorted(layers.keys()):
        y  = MARGIN + layer_idx*(NODE_H+LAYER_GAP) - 10
        lh = NODE_H + 20
        parts.append(
            f'<rect x="{MARGIN//2}" y="{y}" width="{svg_w-MARGIN}" height="{lh}" '
            f'rx="6" fill="#F8F9FA" stroke="#E5E7EB" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{MARGIN//2+8}" y="{y+14}" fill="#64748B" '
            f'font-size="10" font-weight="600">{LAYER_LABELS.get(layer_idx,"")}</text>'
        )

    # Edges (draw before nodes)
    for e in edges:
        if e.source not in positions or e.target not in positions:
            continue
        x1,y1 = positions[e.source]
        x2,y2 = positions[e.target]
        is_doc = e.style == "dashed"
        stroke_col = "#C0392B" if is_doc else "#888"
        dash = 'stroke-dasharray="5,3"' if is_doc else ""
        marker = "url(#arr2)" if is_doc else "url(#arr)"
        # Bezier curve
        mx, my = (x1+x2)/2, (y1+y2)/2
        parts.append(
            f'<path d="M{x1},{y1+NODE_H//2} C{x1},{my} {x2},{my} {x2},{y2-NODE_H//2}" '
            f'fill="none" stroke="{stroke_col}" stroke-width="1.2" {dash} '
            f'marker-end="{marker}"/>'
        )
        if e.label and not is_doc:
            parts.append(
                f'<text x="{mx}" y="{my-4}" fill="#555" font-size="7" '
                f'text-anchor="middle">{e.label[:25]}</text>'
            )

    # Nodes
    for n in nodes:
        if n.id not in positions:
            continue
        cx, cy = positions[n.id]
        x = cx - NODE_W/2; y = cy - NODE_H/2
        fill   = FILL.get(n.category,"#fff")
        stroke = STROKE.get(n.category,"#888")
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{NODE_W}" height="{NODE_H}" '
            f'rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
        )
        # Label (multi-line)
        label_lines = n.label.split("\n")
        text_y = cy - (len(label_lines)-1)*7
        for i, line in enumerate(label_lines):
            parts.append(
                f'<text x="{cx:.1f}" y="{text_y + i*13:.1f}" fill="{stroke}" '
                f'font-size="9" font-weight="600" text-anchor="middle">{line}</text>'
            )
        if n.value:
            parts.append(
                f'<text x="{cx:.1f}" y="{cy+NODE_H//2-8:.1f}" fill="{stroke}" '
                f'font-size="8" text-anchor="middle">{n.value} {n.unit}</text>'
            )

    parts.append('</svg>')
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def generate_parameter_dependency_graph(model, cs) -> dict:
    """
    Build and populate the parameter dependency graph.

    Returns:
        {
          "nodes": [{"id","label","category","layer","value","unit"}, ...],
          "edges": [{"source","target","label","style"}, ...],
          "mermaid": str,   # .mmd content
          "svg":    str,    # self-contained SVG
          "stats":  {...},
        }
    """
    nodes_raw, edges = build_graph()
    nodes = populate_graph_values(nodes_raw, model, cs)

    mermaid = render_mermaid(nodes, edges)
    svg     = render_svg(nodes, edges)

    # Count by category
    cats = {}
    for n in nodes:
        cats[n.category] = cats.get(n.category, 0) + 1

    return {
        "nodes":   [{"id":n.id,"label":n.label,"category":n.category,
                     "layer":n.layer,"value":n.value,"unit":n.unit} for n in nodes],
        "edges":   [{"source":e.source,"target":e.target,
                     "label":e.label,"style":e.style} for e in edges],
        "mermaid": mermaid,
        "svg":     svg,
        "stats": {
            "total_nodes":  len(nodes),
            "total_edges":  len(edges),
            "input_nodes":  cats.get("input", 0),
            "calc_nodes":   cats.get("calculated", 0),
            "fn_nodes":     cats.get("function", 0),
            "doc_nodes":    cats.get("document", 0),
            "layers":       max(n.layer for n in nodes) + 1,
        }
    }


def save_dependency_graph(model, cs, output_dir: Path) -> dict[str, Path]:
    """Save Mermaid, SVG and JSON graph files. Returns {format: path}."""
    graph = generate_parameter_dependency_graph(model, cs)
    paths: dict[str, Path] = {}

    mmd_path = output_dir / "parameter_dependency_graph.mmd"
    mmd_path.write_text(graph["mermaid"], encoding="utf-8")
    paths["mermaid"] = mmd_path

    svg_path = output_dir / "parameter_dependency_graph.svg"
    svg_path.write_text(graph["svg"], encoding="utf-8")
    paths["svg"] = svg_path

    json_path = output_dir / "parameter_dependency_graph.json"
    json_path.write_text(
        json.dumps({"nodes": graph["nodes"], "edges": graph["edges"],
                    "stats": graph["stats"]}, indent=2),
        encoding="utf-8"
    )
    paths["json"] = json_path

    return paths
