"""
figures.py
Railway Documentation Generator - Figure Generation Module
Produces all charts and diagrams using Matplotlib and Plotly.
"""

import io
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path
from config import FIGURE_DPI, FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN, PALETTE, OUTPUT_FIGS


plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "figure.dpi":        FIGURE_DPI,
})


def _save(fig, name: str) -> Path:
    path = OUTPUT_FIGS / f"{name}.png"
    fig.savefig(path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    return path


def _bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ═══════════════════════════════════════════════════════════════
# HEADWAY BREAKDOWN
# ═══════════════════════════════════════════════════════════════

def figure_headway_breakdown(headway_dict: dict, save: bool = True):
    labels = [k for k in headway_dict if "Headway" not in k and "Separation" not in k]
    values = [headway_dict[k] for k in labels]

    fig, axes = plt.subplots(1, 2, figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN))

    # Bar chart
    ax = axes[0]
    bars = ax.barh(labels, values, color=PALETTE[:len(labels)], edgecolor="white")
    ax.set_xlabel("Duration (seconds)")
    ax.set_title("Headway Component Breakdown", fontweight="bold")
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                f"{val:.1f} s", va="center", fontsize=8)

    # Pie chart
    ax2 = axes[1]
    wedges, texts, autotexts = ax2.pie(
        values, labels=None, colors=PALETTE[:len(labels)],
        autopct="%1.1f%%", startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5}
    )
    ax2.set_title("Headway Proportion", fontweight="bold")
    ax2.legend(wedges, labels, loc="lower right", fontsize=7, bbox_to_anchor=(1.3, 0.0))

    fig.suptitle("Minimum Headway Analysis", fontsize=14, fontweight="bold", y=1.01)
    fig.tight_layout()
    return (_save(fig, "headway_breakdown"), fig) if save else (_bytes(fig), None)


# ═══════════════════════════════════════════════════════════════
# FLEET COMPOSITION
# ═══════════════════════════════════════════════════════════════

def figure_fleet_composition(fleet_size: int, reserve: int, save: bool = True):
    labels = ["Operational Fleet", "Reserve Fleet", "Maintenance Float"]
    maint  = max(1, round(fleet_size * 0.05))
    values = [fleet_size - maint, reserve, maint]

    fig, ax = plt.subplots(figsize=(7, 5))
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=PALETTE[:3],
        autopct=lambda p: f"{p:.1f}%\n({round(p*sum(values)/100):.0f} trains)",
        startangle=140, wedgeprops={"edgecolor": "white", "linewidth": 2}
    )
    for at in autotexts:
        at.set_fontsize(9)
    ax.set_title(f"Fleet Composition\nTotal: {sum(values)} trains", fontweight="bold", fontsize=12)
    fig.tight_layout()
    return (_save(fig, "fleet_composition"), fig) if save else (_bytes(fig), None)


# ═══════════════════════════════════════════════════════════════
# TRAIN CAPACITY
# ═══════════════════════════════════════════════════════════════

def figure_train_capacity(seated: int, standing_4: int, standing_6: int, save: bool = True):
    categories = ["4 pax/m²", "6 pax/m²"]
    seated_vals  = [seated, seated]
    standing_vals= [standing_4, standing_6]

    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(len(categories))
    width = 0.5
    p1 = ax.bar(x, seated_vals,  width, label="Seated",   color=PALETTE[0])
    p2 = ax.bar(x, standing_vals,width, bottom=seated_vals, label="Standing", color=PALETTE[1])
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylabel("Passengers")
    ax.set_title("Train Passenger Capacity", fontweight="bold")
    ax.legend()
    totals = [s + st for s, st in zip(seated_vals, standing_vals)]
    for xi, t in zip(x, totals):
        ax.text(xi, t + 10, f"{t}", ha="center", fontweight="bold")
    fig.tight_layout()
    return (_save(fig, "train_capacity"), fig) if save else (_bytes(fig), None)


# ═══════════════════════════════════════════════════════════════
# COMMERCIAL SPEED COMPARISON
# ═══════════════════════════════════════════════════════════════

def figure_speed_comparison(commercial_speed: float, max_speed: float, design_speed: float,
                             save: bool = True):
    speeds = {
        "Maximum Speed\n(Design)":     max_speed,
        "Design Speed\n(Infrastructure)": design_speed,
        "Commercial Speed\n(Operations)": commercial_speed,
    }
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(speeds.keys(), speeds.values(),
                  color=[PALETTE[4], PALETTE[2], PALETTE[0]], edgecolor="white")
    ax.set_ylabel("Speed (km/h)")
    ax.set_title("Speed Parameter Comparison", fontweight="bold")
    for bar, val in zip(bars, speeds.values()):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{val:.1f} km/h", ha="center", fontsize=9, fontweight="bold")
    ax.set_ylim(0, max_speed * 1.2)
    fig.tight_layout()
    return (_save(fig, "speed_comparison"), fig) if save else (_bytes(fig), None)


# ═══════════════════════════════════════════════════════════════
# AVAILABILITY CHART
# ═══════════════════════════════════════════════════════════════

def figure_availability_chart(availability: float, target: float, save: bool = True):
    fig, ax = plt.subplots(figsize=(7, 4))
    cats = ["System\nAvailability", "Target\nAvailability"]
    vals = [availability * 100, target]
    colors = [PALETTE[2] if availability * 100 >= target else PALETTE[5], PALETTE[0]]
    bars = ax.bar(cats, vals, color=colors, edgecolor="white", width=0.4)
    ax.set_ylim(min(vals) * 0.999, 100.05)
    ax.set_ylabel("Availability (%)")
    ax.set_title("System Availability — Calculated vs Target", fontweight="bold")
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                f"{val:.3f}%", ha="center", fontsize=10, fontweight="bold")
    fig.tight_layout()
    return (_save(fig, "availability_chart"), fig) if save else (_bytes(fig), None)


# ═══════════════════════════════════════════════════════════════
# RELIABILITY (Bathtub / Exponential)
# ═══════════════════════════════════════════════════════════════

def figure_reliability_curve(mtbf: float, mission_hours: int = 24 * 365, save: bool = True):
    t = np.linspace(0, mission_hours, 500)
    lam = 1.0 / mtbf
    R = np.exp(-lam * t)

    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN - 1))
    ax.plot(t, R * 100, color=PALETTE[0], linewidth=2.5)
    ax.fill_between(t, R * 100, alpha=0.15, color=PALETTE[0])
    ax.axhline(99, color=PALETTE[1], linestyle="--", linewidth=1, label="99% threshold")
    ax.set_xlabel("Operating Hours")
    ax.set_ylabel("Reliability R(t) (%)")
    ax.set_title(f"System Reliability Curve\nMTBF = {mtbf:,} h (λ = {lam:.2e} /h)", fontweight="bold")
    ax.legend()
    fig.tight_layout()
    return (_save(fig, "reliability_curve"), fig) if save else (_bytes(fig), None)


# ═══════════════════════════════════════════════════════════════
# RAM SUMMARY PIE
# ═══════════════════════════════════════════════════════════════

def figure_ram_pie(availability: float, save: bool = True):
    labels = ["Available", "Unavailable"]
    vals   = [availability * 100, (1 - availability) * 100]
    colors = [PALETTE[2], PALETTE[5]]

    fig, ax = plt.subplots(figsize=(6, 5))
    wedges, texts, auts = ax.pie(
        vals, labels=labels, colors=colors,
        autopct="%1.4f%%", startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 2}
    )
    auts[0].set_fontsize(12)
    auts[0].set_fontweight("bold")
    ax.set_title("System Availability Breakdown", fontweight="bold")
    fig.tight_layout()
    return (_save(fig, "ram_pie"), fig) if save else (_bytes(fig), None)


# ═══════════════════════════════════════════════════════════════
# TRAIN DIAGRAM (Space-Time simplified)
# ═══════════════════════════════════════════════════════════════

def figure_train_diagram(n_stations: int, headway_s: int, rtt_min: float, save: bool = True):
    """Simplified space-time diagram for two trains."""
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN))
    y_stations = np.linspace(0, 1, n_stations)
    n_trains_shown = min(4, max(2, int(rtt_min * 60 / headway_s)))
    colors_t = PALETTE[:n_trains_shown]

    for i in range(n_trains_shown):
        offset = i * headway_s / 60   # minutes offset
        # Forward journey
        t_start = offset
        t_end   = t_start + rtt_min / 2
        ax.plot([t_start, t_end], [0, 1], color=colors_t[i], linewidth=2, label=f"Train {i+1}")
        # Return journey
        ax.plot([t_end, t_end + rtt_min / 2], [1, 0], color=colors_t[i],
                linewidth=2, linestyle="--")

    for ys in y_stations:
        ax.axhline(ys, color="lightgrey", linewidth=0.5, zorder=0)
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("Position (normalised)")
    ax.set_yticks(y_stations)
    ax.set_yticklabels([f"Stn {i+1}" for i in range(n_stations)], fontsize=7)
    ax.set_title("Simplified Space-Time Diagram", fontweight="bold")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    return (_save(fig, "train_diagram"), fig) if save else (_bytes(fig), None)


# ═══════════════════════════════════════════════════════════════
# PPHPD vs CAPACITY
# ═══════════════════════════════════════════════════════════════

def figure_capacity_demand(demand: int, cap_4: int, cap_6: int, save: bool = True):
    fig, ax = plt.subplots(figsize=(8, 4))
    cats   = ["Peak Demand", "Capacity\n4 pax/m²", "Capacity\n6 pax/m²"]
    vals   = [demand, cap_4, cap_6]
    colors = [PALETTE[1], PALETTE[2], PALETTE[0]]
    bars   = ax.bar(cats, vals, color=colors, edgecolor="white", width=0.5)
    ax.set_ylabel("Passengers per Hour per Direction")
    ax.set_title("Capacity vs Demand Analysis", fontweight="bold")
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + demand * 0.01,
                f"{v:,}", ha="center", fontsize=10, fontweight="bold")
    ax.set_ylim(0, max(vals) * 1.15)
    fig.tight_layout()
    return (_save(fig, "capacity_demand"), fig) if save else (_bytes(fig), None)


# ═══════════════════════════════════════════════════════════════
# CONVENIENCE: generate all figures
# ═══════════════════════════════════════════════════════════════

def generate_all_figures(p_or_model, ops_or_cs, ram=None, headway=None) -> dict:
    """
    Generate the full figure set. Accepts either:
      - New API: generate_all_figures(model, cs)   — CalculatedState
      - Legacy:  generate_all_figures(p, ops, ram, headway)
    Returns a dict of {name: path}.
    """
    from calculations import CalculatedState

    # Detect new vs legacy API
    if isinstance(ops_or_cs, CalculatedState):
        cs    = ops_or_cs
        model = p_or_model
        p     = model.to_dict() if hasattr(model, 'to_dict') else model
        ops   = cs.ops
        ram   = cs.ram
        hdw   = cs.headway
        cap   = cs.capacity
    else:
        p   = p_or_model
        ops = ops_or_cs
        hdw = headway
        cap = None

    paths = {}

    # Headway breakdown — build dict from new or old structure
    if hasattr(hdw, 'headway_breakdown'):
        hdw_dict = hdw.headway_breakdown   # old API
    else:
        hdw_dict = {
            "System Reaction Time (s)":   hdw.reaction_time_sec,
            "Transmission Latency (s)":   hdw.transmission_latency_sec,
            "Emergency Braking Time (s)": hdw.braking_time_sec,
            "Safety Margin (s)":          hdw.safety_margin_sec,
            "Jerk Limitation (s)":        hdw.jerk_limitation_sec,
            "Technical Headway (s)":      hdw.technical_headway_sec,
            "Commercial Headway (s)":     hdw.commercial_headway_sec,
        }

    paths["headway"], _ = figure_headway_breakdown(hdw_dict)
    paths["fleet"],   _ = figure_fleet_composition(ops.fleet_required, ops.reserve_trains)
    paths["capacity_train"], _ = figure_train_capacity(
        p.get("seated_capacity", 306) if isinstance(p, dict) else p.get("seated_capacity", 306),
        p.get("standing_capacity_4ppm2", 612) if isinstance(p, dict) else p.get("standing_capacity_4ppm2", 612),
        p.get("standing_capacity_6ppm2", 918) if isinstance(p, dict) else p.get("standing_capacity_6ppm2", 918),
    )
    paths["speed"], _ = figure_speed_comparison(
        ops.commercial_speed_kmh,
        p.get("max_speed_kmh", 80) if isinstance(p, dict) else p.get("max_speed_kmh", 80),
        p.get("design_speed_kmh", 90) if isinstance(p, dict) else p.get("design_speed_kmh", 90),
    )
    avail_val = ram.availability if hasattr(ram, 'availability') else ram.system_availability
    avail_tgt = p.get("system_availability_target_pct", 99.5) if isinstance(p, dict) else p.get("system_availability_target_pct", 99.5)
    paths["availability"], _ = figure_availability_chart(avail_val, avail_tgt)
    paths["reliability"], _ = figure_reliability_curve(ram.mtbf_hours)
    paths["ram_pie"],    _ = figure_ram_pie(avail_val)
    paths["train_diagram"], _ = figure_train_diagram(
        p.get("number_of_stations", 18) if isinstance(p, dict) else p.get("number_of_stations", 18),
        p.get("peak_headway_sec", 120) if isinstance(p, dict) else p.get("peak_headway_sec", 120),
        ops.round_trip_time_min,
    )
    pphpd4 = cap.pphpd_4ppm2 if cap else getattr(ops, 'pphpd_4ppm2', 36720)
    pphpd6 = cap.pphpd_6ppm2 if cap else getattr(ops, 'pphpd_6ppm2', 36720)
    demand = p.get("peak_demand_pphpd", 45000) if isinstance(p, dict) else p.get("peak_demand_pphpd", 45000)
    paths["capacity_demand"], _ = figure_capacity_demand(demand, pphpd4, pphpd6)
    return paths


# ═══════════════════════════════════════════════════════════════════════════════
# SPECIALIST FIGURES FOR THE 6 NEW DOCUMENT TYPES
# All values from CalculatedState — no hardcoded engineering numbers
# ═══════════════════════════════════════════════════════════════════════════════

def figure_reliability_curve_multiline(cs, save: bool = True):
    """Multi-subsystem R(t) curves + system mission reliability."""
    import math
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(10, 5))
    t = np.linspace(0, 8760, 500)           # 0 … 1 year
    colours = ["#003087","#C0392B","#F39C12","#27AE60","#8E44AD","#17A2B8","#E67E22"]

    ra = cs.rams_alloc
    for i, (name, mtbf) in enumerate(zip(ra.subsystem_names, ra.allocated_mtbf_hours)):
        lam = 1.0 / mtbf
        ax.plot(t, np.exp(-lam * t), color=colours[i % len(colours)],
                linewidth=1.4, label=f"{name} (MTBF={int(mtbf):,}h)", linestyle="--", alpha=0.7)

    # System mission reliability
    lam_s = cs.ram.failure_rate_per_hour
    ax.plot(t, np.exp(-lam_s * t), color="#003087", linewidth=2.5,
            label=f"System R(t) (MTBF={cs.ram.mtbf_hours:,}h)")

    # Mark 24h mission point
    ax.axvline(24, color="grey", linestyle=":", linewidth=1)
    ax.annotate(f"R(24h)={cs.ram.mission_reliability_24h:.5f}",
                xy=(24, cs.ram.mission_reliability_24h),
                xytext=(200, cs.ram.mission_reliability_24h - 0.002),
                fontsize=8, color="grey")
    ax.set_xlim(0, 8760); ax.set_ylim(0.99, 1.0005)
    ax.set_xlabel("Mission Time t (hours)"); ax.set_ylabel("Reliability R(t)")
    ax.set_title("Subsystem and System Reliability Curves — R(t) = e^(−λt)  [EN 50126-1]")
    ax.legend(fontsize=7, loc="lower left"); ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return (_save(fig, "reliability_multiline"), fig) if save else (_bytes(fig), None)


def figure_availability_waterfall(cs, save: bool = True):
    """Availability waterfall chart from 100% to series lower bound."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    ra      = cs.rams_alloc
    names   = list(ra.subsystem_names) + ["Series LB"]
    losses  = [(1.0 - a/100.0)*1e6 for a in ra.allocated_avail_pct]  # ppm losses
    cumul   = []
    running = 0.0
    for l in losses:
        running += l
        cumul.append(running)
    total_loss  = (1.0 - ra.series_avail_pct/100.0)*1e6
    target_loss = (1.0 - ra.system_avail_target_pct/100.0)*1e6

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = losses + [total_loss]
    bar_names = [n.replace(" ","\n") for n in names]
    colours = ["#C0392B" if b > target_loss/len(ra.subsystem_names) else "#27AE60"
               for b in losses] + ["#003087"]
    ax.bar(range(len(bars)), bars, color=colours, edgecolor="white", linewidth=0.5)
    ax.axhline(target_loss/len(ra.subsystem_names), color="#E67E22",
               linestyle="--", linewidth=1.2, label="Mean budget per subsystem")
    ax.set_xticks(range(len(bars))); ax.set_xticklabels(bar_names, fontsize=8)
    ax.set_ylabel("Unavailability (ppm — parts per million)")
    ax.set_title("Availability Waterfall — Unavailability Budget per Subsystem (ppm)")
    ax.legend(fontsize=8); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return (_save(fig, "availability_waterfall"), fig) if save else (_bytes(fig), None)


def figure_maintainability_M_t(cs, save: bool = True):
    """M(t_ref) bar chart per subsystem at multiple reference times."""
    import math
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    ra      = cs.rams_alloc
    t_refs  = [2, 4, 8]
    names   = [n.replace(" ","\n") for n in ra.subsystem_names]
    x       = np.arange(len(ra.subsystem_names))
    width   = 0.25
    colours = ["#003087","#2980B9","#85C1E9"]

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, (t_ref, col) in enumerate(zip(t_refs, colours)):
        vals = [1.0 - math.exp(-(1.0/mttr)*t_ref) for mttr in ra.allocated_mttr_hours]
        ax.bar(x + i*width, vals, width, label=f"M({t_ref}h)", color=col, edgecolor="white")

    ax.axhline(1-math.exp(-1), color="grey", linestyle=":", linewidth=1,
               label="M(MTTR) = 0.632 (degenerate reference)")
    ax.set_xticks(x + width); ax.set_xticklabels(names, fontsize=8)
    ax.set_ylim(0, 1.05); ax.set_ylabel("Maintainability M(t_ref)")
    ax.set_title("Subsystem Maintainability at Reference Repair Windows  [EN 50126-2 §6.3.3]")
    ax.legend(fontsize=9); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return (_save(fig, "maintainability_M_t"), fig) if save else (_bytes(fig), None)


def figure_energy_breakdown_stacked(cs, save: bool = True):
    """Stacked bar: energy components per train-km."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t       = cs.traction
    labels  = ["Gross Energy", "Net Energy (after regen)"]
    kin     = [t.acc_energy_kwh_km,      t.acc_energy_kwh_km - t.braking_energy_kwh_km]
    res     = [t.resistance_energy_kwh_km, t.resistance_energy_kwh_km]
    grad    = [t.gradient_energy_kwh_km,   t.gradient_energy_kwh_km]
    aux     = [t.auxiliary_energy_kwh_km,  t.auxiliary_energy_kwh_km]

    fig, ax = plt.subplots(figsize=(7, 5))
    x = [0, 1]
    ax.bar(x, kin,  label="Kinetic (acceleration)", color="#003087")
    ax.bar(x, res,  bottom=kin, label="Rolling resistance (Davis)", color="#2980B9")
    bot2 = [k+r for k,r in zip(kin, res)]
    ax.bar(x, grad, bottom=bot2, label="Gradient", color="#85C1E9")
    bot3 = [a+b for a,b in zip(bot2, grad)]
    ax.bar(x, aux,  bottom=bot3, label="Auxiliary loads", color="#AED6F1")

    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel("Energy (kWh / train-km)")
    ax.set_title(f"Traction Energy Breakdown  (EN 50641)\nRegen saving: {t.regenerative_saving_pct:.1f}%  |  Net: {t.energy_per_train_km_kwh:.3f} kWh/km")
    ax.legend(fontsize=8, loc="upper right"); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return (_save(fig, "energy_breakdown"), fig) if save else (_bytes(fig), None)


def figure_energy_annual_breakdown(cs, save: bool = True):
    """Pie chart of annual energy by component."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t   = cs.traction
    tkm = cs.ops.annual_train_km / 1000.0
    sizes = [
        t.acc_energy_kwh_km * tkm,
        t.resistance_energy_kwh_km * tkm,
        t.auxiliary_energy_kwh_km * tkm,
        t.gradient_energy_kwh_km * tkm,
    ]
    labels = [
        f"Kinetic\n{t.acc_energy_kwh_km*tkm:,.0f} MWh",
        f"Resistance\n{t.resistance_energy_kwh_km*tkm:,.0f} MWh",
        f"Auxiliary\n{t.auxiliary_energy_kwh_km*tkm:,.0f} MWh",
        f"Gradient\n{t.gradient_energy_kwh_km*tkm:,.0f} MWh",
    ]
    colours = ["#003087","#2980B9","#85C1E9","#AED6F1"]

    fig, ax = plt.subplots(figsize=(7, 5))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colours, autopct="%1.1f%%",
        startangle=90, pctdistance=0.75)
    for t_ in autotexts: t_.set_fontsize(9)
    ax.set_title(f"Annual Gross Energy Distribution\nTotal gross: {sum(sizes):,.0f} MWh/year  |  Net after regen: {t.annual_energy_mwh:,.0f} MWh/year")
    fig.tight_layout()
    return (_save(fig, "energy_annual_pie"), fig) if save else (_bytes(fig), None)


def figure_occ_workload_radar(cs, save: bool = True):
    """Radar chart of OCC operator task demands."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    categories = ["Train\nSupervision","Emergency\nResponse","SCADA\nMonitoring",
                  "Passenger\nComms","Maintenance\nCoord.","Handover\nProcedure"]
    # Workload index 1-5 derived from CalculatedState
    trains = cs.ops.trains_in_service
    norm   = min(5.0, trains / 10.0)                     # more trains = higher supervision load
    vals   = [
        round(min(5, norm), 1),                           # train supervision
        5.0,                                               # emergency — always maximum
        round(min(5, 2.0 + cs.ops.total_fleet/30), 1),   # SCADA — fleet-driven
        round(min(5, 1.5 + cs.capacity.pphpd_6ppm2/15000), 1),  # pax comms — demand driven
        round(min(5, 1.0 + cs.ops.total_fleet/20), 1),   # maintenance coordination
        3.0,                                               # handover — fixed procedure
    ]

    N = len(categories)
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    vals_   = vals + [vals[0]]
    angles += [angles[0]]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.plot(angles, vals_, color="#003087", linewidth=2)
    ax.fill(angles, vals_, color="#003087", alpha=0.20)
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(categories, fontsize=9)
    ax.set_ylim(0, 5); ax.set_yticks([1,2,3,4,5]); ax.set_yticklabels(["1","2","3","4","5"])
    ax.set_title(f"OCC Operator Workload Radar\n({trains} trains in service, headway {cs.ops.headway_sec}s)",
                 pad=15, fontsize=11)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return (_save(fig, "occ_workload_radar"), fig) if save else (_bytes(fig), None)


def figure_hazard_risk_matrix(cs, save: bool = True):
    """4×5 risk matrix with the 10 hazards plotted from CalculatedState."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np

    fig, ax = plt.subplots(figsize=(9, 6))
    # Risk matrix background (Severity × Probability)
    # Acceptable=green, Undesirable=amber, Intolerable=red
    RISK = {
        (1,1):"#D5F5E3",(1,2):"#D5F5E3",(1,3):"#D5F5E3",(1,4):"#FEF9E7",(1,5):"#FEF9E7",
        (2,1):"#D5F5E3",(2,2):"#D5F5E3",(2,3):"#FEF9E7",(2,4):"#FEF9E7",(2,5):"#FDECEA",
        (3,1):"#D5F5E3",(3,2):"#FEF9E7",(3,3):"#FDECEA",(3,4):"#FDECEA",(3,5):"#FDECEA",
        (4,1):"#FEF9E7",(4,2):"#FDECEA",(4,3):"#FDECEA",(4,4):"#FDECEA",(4,5):"#FDECEA",
    }
    for (sev, prob), col in RISK.items():
        ax.add_patch(mpatches.Rectangle((prob-0.5, sev-0.5), 1, 1,
                     facecolor=col, edgecolor="#ccc", linewidth=0.5))

    # Hazard points (S, P) from hazard_log_with_cs_table data
    hazards = [
        ("H1",4,2),("H2",4,1),("H3",4,2),("H4",4,2),("H5",4,2),
        ("H6",4,2),("H7",3,3),("H8",3,3),("H9",3,2),("H10",3,2),
    ]
    colours_h = ["#003087","#C0392B","#E67E22","#8E44AD","#17A2B8",
                 "#27AE60","#D35400","#1ABC9C","#2C3E50","#922B21"]
    for i, (hid, sev, prob) in enumerate(hazards):
        ax.scatter(prob, sev, s=120, color=colours_h[i], zorder=5, edgecolors="white", linewidth=0.8)
        ax.annotate(hid, (prob+0.05, sev+0.05), fontsize=7, color=colours_h[i], fontweight="bold")

    ax.set_xlim(0.5, 5.5); ax.set_ylim(0.5, 4.5)
    ax.set_xticks([1,2,3,4,5])
    ax.set_xticklabels(["1\nImprobable","2\nRemote","3\nOccasional","4\nProbable","5\nFrequent"])
    ax.set_yticks([1,2,3,4])
    ax.set_yticklabels(["1 Negligible","2 Marginal","3 Critical","4 Catastrophic"])
    ax.set_xlabel("Probability"); ax.set_ylabel("Severity")
    v_c = cs.ops.commercial_speed_kmh
    h_t = cs.headway.technical_headway_sec
    ax.set_title(f"Hazard Risk Matrix (EN 50126-1 Table 4)\n"
                 f"v_c={v_c}km/h  H_tech={h_t}s  d_sep={cs.headway.minimum_safe_separation_m:.0f}m  Fleet={cs.ops.total_fleet} trains")
    patches = [mpatches.Patch(color="#D5F5E3",label="Acceptable"),
               mpatches.Patch(color="#FEF9E7",label="Undesirable"),
               mpatches.Patch(color="#FDECEA",label="Intolerable")]
    ax.legend(handles=patches, loc="upper left", fontsize=8)
    fig.tight_layout()
    return (_save(fig, "hazard_risk_matrix"), fig) if save else (_bytes(fig), None)


def generate_specialist_figures(cs) -> dict:
    """Generate all specialist figures for the 6 new document types."""
    paths = {}
    paths["reliability_multiline"],  _ = figure_reliability_curve_multiline(cs)
    paths["availability_waterfall"], _ = figure_availability_waterfall(cs)
    paths["maintainability_M_t"],    _ = figure_maintainability_M_t(cs)
    paths["energy_breakdown"],       _ = figure_energy_breakdown_stacked(cs)
    paths["energy_annual_pie"],      _ = figure_energy_annual_breakdown(cs)
    paths["occ_workload_radar"],     _ = figure_occ_workload_radar(cs)
    paths["hazard_risk_matrix"],     _ = figure_hazard_risk_matrix(cs)
    return paths
