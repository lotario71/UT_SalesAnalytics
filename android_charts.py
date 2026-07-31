"""Gráficas matplotlib para la app Android (tema oscuro)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

BG = "#111827"
PANEL = "#1f2937"
TEXT = "#e5e7eb"
MUTED = "#94a3b8"
GRID = "#334155"
BLUE = "#3b82f6"
TEAL = "#14b8a6"
GREEN = "#22c55e"
RED = "#ef4444"

SERVICE_COLORS = {
    "Hotel Services": TEAL,
    "Transfer Services": BLUE,
    "Car Services": "#f59e0b",
    "Tour Services": "#a855f7",
    "Miscellaneous Services": "#64748b",
    "Flight Services": "#06b6d4",
    "Other": "#6b7280",
}


def _style_ax(ax, title: str, ylabel: str = ""):
    ax.set_facecolor(PANEL)
    ax.set_title(title, color=TEXT, fontsize=12, pad=10)
    if ylabel:
        ax.set_ylabel(ylabel, color=MUTED)
    ax.tick_params(colors=MUTED)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.grid(True, color=GRID, alpha=0.45)


def save_vs_paid(all_total: float, paid_total: float, path: str | Path, subtitle: str = ""):
    fig, ax = plt.subplots(figsize=(6.5, 4.2), facecolor=BG)
    _style_ax(ax, f"Todas vs pagadas{(' · ' + subtitle) if subtitle else ''}", "Ventas (USD)")
    labels = ["Todas", "Pagadas"]
    values = [all_total, paid_total]
    bars = ax.bar(labels, values, color=[BLUE, TEAL], width=0.55)
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + max(values + [1]) * 0.03,
            f"${val:,.0f}",
            ha="center",
            color=TEXT,
            fontweight="bold",
        )
    if all_total > 0:
        pct = paid_total / all_total * 100
        b = bars[1]
        ax.text(
            b.get_x() + b.get_width() / 2,
            max(b.get_height() * 0.5, max(values) * 0.08),
            f"{pct:.1f}%",
            ha="center",
            va="center",
            color="white",
            fontsize=14,
            fontweight="bold",
        )
    fig.tight_layout()
    fig.savefig(path, dpi=140, facecolor=BG)
    plt.close(fig)


def save_service_pies(all_items, paid_items, path: str | Path, subtitle: str = ""):
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 4.2), facecolor=BG)
    for ax, items, title in (
        (axes[0], all_items, "Todas (SOAP)"),
        (axes[1], paid_items, "Pagadas (SOAP)"),
    ):
        ax.set_facecolor(BG)
        if not items:
            ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", color=MUTED)
            ax.set_title(title, color=TEXT)
            ax.axis("off")
            continue
        labels = [n for n, _ in items]
        sizes = [v for _, v in items]
        colors = [SERVICE_COLORS.get(n, "#6b7280") for n in labels]
        wedges, *_ = ax.pie(
            sizes,
            colors=colors,
            startangle=90,
            wedgeprops={"linewidth": 1, "edgecolor": BG},
        )
        ax.set_title(title, color=TEXT, fontsize=11)
        total = sum(sizes) or 1
        legend = [f"{n}: ${v:,.0f} ({v/total*100:.1f}%)" for n, v in items]
        ax.legend(
            wedges,
            legend,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.15),
            fontsize=7,
            frameon=False,
            labelcolor=TEXT,
        )
    fig.suptitle(f"Tipos de servicio{(' · ' + subtitle) if subtitle else ''}", color=TEXT, fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=140, facecolor=BG, bbox_inches="tight")
    plt.close(fig)


def save_behavior_monthly(all_months, paid_months, path: str | Path, year: int):
    fig, ax = plt.subplots(figsize=(7.2, 4.2), facecolor=BG)
    _style_ax(ax, f"Comportamiento · {year} · Meses (SOAP)", "USD")
    months = list(range(1, 13))
    all_map = dict(all_months)
    paid_map = dict(paid_months)
    y_all = [all_map.get(m, 0.0) for m in months]
    y_paid = [paid_map.get(m, 0.0) for m in months]
    ax.plot(months, y_all, marker="o", color=BLUE, linewidth=2, label="Todas")
    ax.plot(months, y_paid, marker="o", color=TEAL, linewidth=2, label="Pagadas")
    ax.set_xticks(months)
    ax.set_xticklabels(
        ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    )
    ax.legend(facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT)
    fig.tight_layout()
    fig.savefig(path, dpi=140, facecolor=BG)
    plt.close(fig)


def _filter_pe_history(history: list[dict], year: int | None) -> tuple[list[dict], str]:
    """
    Preferencia: puntos del año pedido.
    Si hay menos de 2, usa las últimas actualizaciones (máx. 15) para no dejar el gráfico vacío.
    """
    import datetime as dt

    if not history:
        return [], "sin datos"
    today = dt.date.today()
    y = year or today.year
    by_date: dict[str, dict] = {}
    for e in history:
        raw = e.get("date")
        if not raw:
            continue
        try:
            d = dt.date.fromisoformat(str(raw)[:10])
        except Exception:
            continue
        by_date[d.isoformat()] = e
    ordered = [by_date[k] for k in sorted(by_date)]
    year_rows = []
    for e in ordered:
        try:
            d = dt.date.fromisoformat(str(e["date"])[:10])
        except Exception:
            continue
        if d.year == y:
            year_rows.append(e)
    if year_rows:
        return year_rows, f"{y}"
    # Sin puntos del año: últimas actualizaciones de respaldo
    return ordered[-15:], "últimas actualizaciones"


def _useful_ylim(vals: list[float], pe: float) -> tuple[float, float, bool]:
    """
    Escala centrada en la parte util del año.
    Los primeros puntos YTD (pocos dias) suelen dispararse a 10k-30k y aplastan el resto.
    """
    if not vals:
        return 0.0, max(pe * 1.5, 100.0), False
    # Usa el 75% final de puntos (orden temporal) para fijar la ventana
    start = max(0, int(len(vals) * 0.2))
    focus = vals[start:] if len(vals) - start >= 4 else vals
    sorted_f = sorted(focus)
    # Percentiles suaves
    def _pct(p: float) -> float:
        if len(sorted_f) == 1:
            return sorted_f[0]
        i = (len(sorted_f) - 1) * p
        lo_i = int(i)
        hi_i = min(lo_i + 1, len(sorted_f) - 1)
        return sorted_f[lo_i] + (sorted_f[hi_i] - sorted_f[lo_i]) * (i - lo_i)

    p10 = _pct(0.10)
    p90 = _pct(0.90)
    lo = min(p10, pe) * 0.85
    hi = max(p90, pe) * 1.25
    # Asegura un rango minimo legible alrededor del PE
    if hi - lo < max(pe * 0.4, 200):
        mid = (lo + hi) / 2 if hi > lo else pe
        span = max(pe * 0.5, 300)
        lo, hi = mid - span / 2, mid + span / 2
    lo = max(0.0, lo)
    clipped = any(v > hi * 1.02 or v < lo * 0.98 for v in vals)
    return lo, hi, clipped


def save_pe_history(
    history: list[dict],
    pe_all: float,
    pe_paid: float,
    path: str | Path,
    year: int | None = None,
    series: str = "all",
):
    """Una sola grafica (movil). series: all | paid."""
    import datetime as dt

    rows, scope = _filter_pe_history(history, year)
    use_paid = series == "paid"
    key = "paid_only_avg" if use_paid else "all_data_avg"
    pe_live = float(pe_paid if use_paid else pe_all)
    pe_field = "pe_value_paid" if use_paid else "pe_value"
    pe_hist = [float(e[pe_field]) for e in rows if e.get(pe_field) is not None]
    today_y = dt.date.today().year
    if pe_hist and year and int(year) != today_y:
        pe = pe_hist[-1]
    else:
        pe = pe_live if pe_live > 0 else (pe_hist[-1] if pe_hist else 0.0)

    label = "Pagadas" if use_paid else "Todas"
    fig, ax = plt.subplots(figsize=(7.2, 5.2), facecolor=BG)
    _style_ax(ax, f"{label} · ritmo diario", "USD / dia")

    if not rows:
        ax.text(0.5, 0.5, "Sin historial", ha="center", va="center", transform=ax.transAxes, color=MUTED)
    else:
        dates = [dt.datetime.fromisoformat(str(e["date"])[:10]) for e in rows]
        vals = []
        for e in rows:
            raw = e.get(key)
            vals.append(None if raw is None else float(raw))
        plot_d = [d for d, v in zip(dates, vals) if v is not None]
        plot_v = [v for v in vals if v is not None]
        if not plot_v:
            ax.text(
                0.5,
                0.5,
                "Sin datos en esta serie\n(en conta historica solo hay Todas)",
                ha="center",
                va="center",
                transform=ax.transAxes,
                color=MUTED,
            )
        else:
            ax.plot(plot_d, plot_v, color="#cbd5e1", linewidth=2.6, zorder=2)
            if len(plot_v) >= 2:
                ax.fill_between(
                    plot_d, plot_v, pe,
                    where=[v >= pe for v in plot_v],
                    color=GREEN, alpha=0.2, interpolate=True,
                )
                ax.fill_between(
                    plot_d, plot_v, pe,
                    where=[v < pe for v in plot_v],
                    color=RED, alpha=0.2, interpolate=True,
                )
            above_x, above_y, below_x, below_y = [], [], [], []
            for d, v in zip(plot_d, plot_v):
                if v >= pe:
                    above_x.append(d)
                    above_y.append(v)
                else:
                    below_x.append(d)
                    below_y.append(v)
            ax.scatter(above_x, above_y, color=GREEN, s=64, zorder=4, edgecolors=BG, linewidths=0.6, label="Sobre PE")
            ax.scatter(below_x, below_y, color=RED, s=64, zorder=4, edgecolors=BG, linewidths=0.6, label="Bajo PE")
            ax.axhline(pe, color=TEAL, linestyle="--", linewidth=2.0, label=f"PE ${pe:,.0f}", zorder=3)
            # Escala util: ignora picos de inicio de año (media YTD muy alta con pocos dias)
            lo, hi, clipped = _useful_ylim(plot_v, pe)
            ax.set_ylim(lo, hi)
            if clipped:
                ax.text(
                    0.01,
                    0.98,
                    "Escala util (picos ene. fuera de vista)",
                    transform=ax.transAxes,
                    va="top",
                    ha="left",
                    color=MUTED,
                    fontsize=8,
                )
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
            if len(plot_d) <= 2:
                from matplotlib.ticker import FixedLocator

                ax.xaxis.set_major_locator(FixedLocator([mdates.date2num(d) for d in plot_d]))
                if len(plot_d) == 1:
                    center = mdates.date2num(plot_d[0])
                    ax.set_xlim(center - 5, center + 5)
            else:
                ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=7))
            ax.legend(fontsize=8, loc="best", facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT)
            # Anotar ultimo punto visible en escala
            last_v = plot_v[-1]
            if lo <= last_v <= hi:
                ax.annotate(
                    f"${last_v:,.0f}",
                    xy=(plot_d[-1], last_v),
                    xytext=(6, 10),
                    textcoords="offset points",
                    color=TEXT,
                    fontsize=10,
                    fontweight="bold",
                )

    fig.suptitle(f"Evolucion PE · {scope}", color=TEXT, fontsize=13, fontweight="bold")
    fig.autofmt_xdate(rotation=25)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=BG)
    plt.close(fig)
