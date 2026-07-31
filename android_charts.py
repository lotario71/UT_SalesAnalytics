"""Graficas con Pillow (tema oscuro). Sin matplotlib/numpy — compatible con Buildozer Android."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (17, 24, 39)
PANEL = (31, 41, 55)
TEXT = (229, 231, 235)
MUTED = (148, 163, 184)
GRID = (51, 65, 85)
BLUE = (59, 130, 246)
TEAL = (20, 184, 166)
GREEN = (34, 197, 94)
RED = (239, 68, 68)

SERVICE_COLORS = {
    "Hotel Services": TEAL,
    "Transfer Services": BLUE,
    "Car Services": (245, 158, 11),
    "Tour Services": (168, 85, 247),
    "Miscellaneous Services": (100, 116, 139),
    "Flight Services": (6, 182, 212),
    "Other": (107, 114, 128),
}

_MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def _font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except Exception:
            return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _new(w: int, h: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (w, h), BG)
    return img, ImageDraw.Draw(img)


def _title(draw, text: str, w: int, y: int = 12):
    font = _font(18)
    tw, _ = _text_size(draw, text, font)
    draw.text(((w - tw) // 2, y), text, fill=TEXT, font=font)


def save_vs_paid(all_total: float, paid_total: float, path: str | Path, subtitle: str = ""):
    w, h = 720, 460
    img, draw = _new(w, h)
    title = "Todas vs pagadas" + (f" · {subtitle}" if subtitle else "")
    _title(draw, title, w)

    left, right, top, bottom = 80, w - 40, 70, h - 50
    draw.rectangle([left, top, right, bottom], fill=PANEL)
    values = [float(all_total or 0), float(paid_total or 0)]
    vmax = max(values + [1.0])
    labels = ["Todas", "Pagadas"]
    colors = [BLUE, TEAL]
    bar_w = 120
    gap = 160
    base_x = left + 120
    for i, (lab, val, col) in enumerate(zip(labels, values, colors)):
        x0 = base_x + i * gap
        bh = int((val / vmax) * (bottom - top - 60))
        y0 = bottom - 20 - bh
        draw.rectangle([x0, y0, x0 + bar_w, bottom - 20], fill=col)
        f = _font(14)
        t = f"${val:,.0f}"
        tw, _ = _text_size(draw, t, f)
        draw.text((x0 + (bar_w - tw) // 2, y0 - 22), t, fill=TEXT, font=f)
        lw, _ = _text_size(draw, lab, f)
        draw.text((x0 + (bar_w - lw) // 2, bottom - 16), lab, fill=MUTED, font=f)
        if i == 1 and values[0] > 0:
            pct = values[1] / values[0] * 100
            pt = f"{pct:.1f}%"
            pw, ph = _text_size(draw, pt, _font(16))
            draw.text(
                (x0 + (bar_w - pw) // 2, y0 + max(bh // 2 - ph // 2, 4)),
                pt,
                fill=(255, 255, 255),
                font=_font(16),
            )
    img.save(path, "PNG")


def save_service_pies(all_items, paid_items, path: str | Path, subtitle: str = ""):
    w, h = 900, 520
    img, draw = _new(w, h)
    _title(draw, "Tipos de servicio" + (f" · {subtitle}" if subtitle else ""), w)

    def _pie(cx: int, cy: int, r: int, items, title: str):
        draw.text((cx - 60, cy - r - 28), title, fill=TEXT, font=_font(14))
        if not items:
            draw.text((cx - 30, cy - 8), "Sin datos", fill=MUTED, font=_font(14))
            return
        total = sum(v for _, v in items) or 1.0
        ang = -90.0
        legend_y = cy + r + 10
        for name, val in items:
            sweep = 360.0 * (val / total)
            color = SERVICE_COLORS.get(name, (107, 114, 128))
            if isinstance(color, str):
                color = _hex_to_rgb(color)
            # Pillow pieslice uses degrees
            draw.pieslice(
                [cx - r, cy - r, cx + r, cy + r],
                start=ang,
                end=ang + sweep,
                fill=color,
                outline=BG,
            )
            ang += sweep
            line = f"{name}: ${val:,.0f} ({val/total*100:.1f}%)"
            draw.text((cx - r, legend_y), line[:42], fill=MUTED, font=_font(11))
            legend_y += 16

    _pie(220, 250, 110, all_items or [], "Todas (SOAP)")
    _pie(680, 250, 110, paid_items or [], "Pagadas (SOAP)")
    img.save(path, "PNG")


def save_behavior_monthly(all_months, paid_months, path: str | Path, year: int):
    w, h = 800, 460
    img, draw = _new(w, h)
    _title(draw, f"Comportamiento · {year} · Meses (SOAP)", w)
    left, right, top, bottom = 60, w - 30, 60, h - 55
    draw.rectangle([left, top, right, bottom], fill=PANEL)

    all_map = dict(all_months or [])
    paid_map = dict(paid_months or [])
    months = list(range(1, 13))
    y_all = [float(all_map.get(m, 0.0)) for m in months]
    y_paid = [float(paid_map.get(m, 0.0)) for m in months]
    vmax = max(y_all + y_paid + [1.0])

    def _pts(vals):
        pts = []
        for i, v in enumerate(vals):
            x = left + 20 + i * ((right - left - 40) / 11)
            y = bottom - 25 - (v / vmax) * (bottom - top - 50)
            pts.append((x, y))
        return pts

    def _polyline(pts, color):
        if len(pts) >= 2:
            draw.line(pts, fill=color, width=3)
        for x, y in pts:
            draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=color)

    _polyline(_pts(y_all), BLUE)
    _polyline(_pts(y_paid), TEAL)
    f = _font(11)
    for i, m in enumerate(months):
        x = left + 20 + i * ((right - left - 40) / 11)
        lab = _MONTHS[m - 1]
        tw, _ = _text_size(draw, lab, f)
        draw.text((x - tw / 2, bottom - 18), lab, fill=MUTED, font=f)
    draw.text((left + 10, top + 8), "Todas", fill=BLUE, font=f)
    draw.text((left + 70, top + 8), "Pagadas", fill=TEAL, font=f)
    img.save(path, "PNG")


def _filter_pe_history(history: list[dict], year: int | None) -> tuple[list[dict], str]:
    if not history:
        return [], "sin datos"
    today = date.today()
    y = year or today.year
    by_date: dict[str, dict] = {}
    for e in history:
        raw = e.get("date")
        if not raw:
            continue
        try:
            d = date.fromisoformat(str(raw)[:10])
        except Exception:
            continue
        by_date[d.isoformat()] = e
    ordered = [by_date[k] for k in sorted(by_date)]
    year_rows = []
    for e in ordered:
        try:
            d = date.fromisoformat(str(e["date"])[:10])
        except Exception:
            continue
        if d.year == y:
            year_rows.append(e)
    if year_rows:
        return year_rows, f"{y}"
    return ordered[-15:], "últimas actualizaciones"


def _useful_ylim(vals: list[float], pe: float) -> tuple[float, float, bool]:
    if not vals:
        return 0.0, max(pe * 1.5, 100.0), False
    start = max(0, int(len(vals) * 0.2))
    focus = vals[start:] if len(vals) - start >= 4 else vals
    sorted_f = sorted(focus)

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
    rows, scope = _filter_pe_history(history, year)
    use_paid = series == "paid"
    key = "paid_only_avg" if use_paid else "all_data_avg"
    pe_live = float(pe_paid if use_paid else pe_all)
    pe_field = "pe_value_paid" if use_paid else "pe_value"
    pe_hist = [float(e[pe_field]) for e in rows if e.get(pe_field) is not None]
    today_y = date.today().year
    if pe_hist and year and int(year) != today_y:
        pe = pe_hist[-1]
    else:
        pe = pe_live if pe_live > 0 else (pe_hist[-1] if pe_hist else 0.0)

    label = "Pagadas" if use_paid else "Todas"
    w, h = 800, 560
    img, draw = _new(w, h)
    _title(draw, f"Evolucion PE · {scope}", w, y=8)
    draw.text((w // 2 - 70, 34), f"{label} · ritmo diario", fill=MUTED, font=_font(13))

    left, right, top, bottom = 55, w - 25, 70, h - 45
    draw.rectangle([left, top, right, bottom], fill=PANEL)

    if not rows:
        draw.text((w // 2 - 50, h // 2), "Sin historial", fill=MUTED, font=_font(16))
        img.save(path, "PNG")
        return

    dates = [datetime.fromisoformat(str(e["date"])[:10]) for e in rows]
    vals = []
    for e in rows:
        raw = e.get(key)
        vals.append(None if raw is None else float(raw))
    plot_d = [d for d, v in zip(dates, vals) if v is not None]
    plot_v = [v for v in vals if v is not None]
    if not plot_v:
        draw.text(
            (w // 2 - 140, h // 2 - 10),
            "Sin datos en esta serie",
            fill=MUTED,
            font=_font(14),
        )
        img.save(path, "PNG")
        return

    lo, hi, clipped = _useful_ylim(plot_v, pe)
    span = max(hi - lo, 1.0)

    def _xy(i: int, v: float) -> tuple[float, float]:
        if len(plot_d) == 1:
            x = (left + right) / 2
        else:
            x = left + 15 + i * ((right - left - 30) / (len(plot_d) - 1))
        y = bottom - 20 - ((v - lo) / span) * (bottom - top - 40)
        return x, y

    # PE line
    pe_y = bottom - 20 - ((pe - lo) / span) * (bottom - top - 40)
    draw.line([(left + 10, pe_y), (right - 10, pe_y)], fill=TEAL, width=2)

    pts = [_xy(i, v) for i, v in enumerate(plot_v)]
    if len(pts) >= 2:
        draw.line(pts, fill=(203, 213, 225), width=3)
    for (x, y), v in zip(pts, plot_v):
        col = GREEN if v >= pe else RED
        draw.ellipse([x - 5, y - 5, x + 5, y + 5], fill=col, outline=BG)

    f = _font(11)
    draw.text((left + 12, top + 8), f"PE ${pe:,.0f}", fill=TEAL, font=f)
    if clipped:
        draw.text((left + 12, top + 26), "Escala util (picos ene. fuera)", fill=MUTED, font=_font(10))

    # x labels
    step = max(1, len(plot_d) // 5)
    for i, d in enumerate(plot_d):
        if i % step != 0 and i != len(plot_d) - 1:
            continue
        x, _ = _xy(i, plot_v[i])
        lab = d.strftime("%d-%b")
        tw, _ = _text_size(draw, lab, f)
        draw.text((x - tw / 2, bottom - 18), lab, fill=MUTED, font=f)

    last_v = plot_v[-1]
    if lo <= last_v <= hi:
        lx, ly = pts[-1]
        t = f"${last_v:,.0f}"
        draw.text((lx + 8, ly - 14), t, fill=TEXT, font=_font(12))

    img.save(path, "PNG")
