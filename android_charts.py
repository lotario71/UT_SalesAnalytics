"""Graficas con Pillow (tema oscuro), verticales a pantalla completa para movil."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (10, 14, 22)
PANEL = (22, 30, 42)
TEXT = (236, 240, 245)
MUTED = (160, 174, 192)
GRID = (51, 65, 85)
BLUE = (59, 130, 246)
TEAL = (20, 184, 166)
GREEN = (34, 197, 94)
RED = (239, 68, 68)
ORANGE = (245, 158, 11)
PURPLE = (168, 85, 247)
CYAN = (6, 182, 212)
SLATE = (100, 116, 139)

SERVICE_COLORS = {
    "Hotel Services": TEAL,
    "Transfer Services": BLUE,
    "Car Services": ORANGE,
    "Tour Services": PURPLE,
    "Miscellaneous Services": SLATE,
    "Flight Services": CYAN,
    "Other": (107, 114, 128),
}

_MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

# Lienzo vertical (casi todo el hueco entre cabecera y bottom nav)
_CW, _CH = 1080, 1680
_S = 2  # PNG nitido al estirar
_ASSETS = Path(__file__).resolve().parent / "assets"
_FONT_FILE = _ASSETS / "chart_font.ttf"


def _font(size: int):
    px = max(12, int(size * _S))
    try:
        if _FONT_FILE.exists():
            return ImageFont.truetype(str(_FONT_FILE), px)
    except Exception:
        pass
    for candidate in (
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/system/fonts/Roboto-Regular.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, px)
        except Exception:
            continue
    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _new(w: int = _CW, h: int = _CH) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (int(w * _S), int(h * _S)), BG)
    return img, ImageDraw.Draw(img)


def _title(draw, text: str, w: int, y: int = 22):
    font = _font(32)
    tw, _ = _text_size(draw, text, font)
    draw.text(((w * _S - tw) // 2, y * _S), text, fill=TEXT, font=font)


def _money(n: float) -> str:
    return f"${n:,.0f}"


def save_vs_paid(all_total: float, paid_total: float, path: str | Path, subtitle: str = ""):
    w, h = _CW, _CH
    img, draw = _new(w, h)
    W, H = img.size
    title = "Todas vs pagadas" + (f" · {subtitle}" if subtitle else "")
    _title(draw, title, w)

    left, right = 70 * _S, W - 70 * _S
    top, bottom = 110 * _S, H - 80 * _S
    draw.rounded_rectangle([left, top, right, bottom], radius=24 * _S, fill=PANEL)
    values = [float(all_total or 0), float(paid_total or 0)]
    vmax = max(values + [1.0])
    labels = ["Todas", "Pagadas"]
    colors = [BLUE, TEAL]
    bar_w = 200 * _S
    gap = 260 * _S
    base_x = left + 150 * _S
    usable = bottom - top - 160 * _S
    for i, (lab, val, col) in enumerate(zip(labels, values, colors)):
        x0 = base_x + i * gap
        bh = int((val / vmax) * usable)
        y0 = bottom - 90 * _S - bh
        draw.rounded_rectangle(
            [x0, y0, x0 + bar_w, bottom - 90 * _S], radius=14 * _S, fill=col
        )
        f = _font(28)
        t = _money(val)
        tw, _ = _text_size(draw, t, f)
        draw.text((x0 + (bar_w - tw) // 2, y0 - 48 * _S), t, fill=TEXT, font=f)
        f2 = _font(26)
        lw, _ = _text_size(draw, lab, f2)
        draw.text((x0 + (bar_w - lw) // 2, bottom - 60 * _S), lab, fill=MUTED, font=f2)
        if i == 1 and values[0] > 0:
            pct = values[1] / values[0] * 100
            pt = f"{pct:.1f}%"
            pf = _font(34)
            pw, ph = _text_size(draw, pt, pf)
            draw.text(
                (x0 + (bar_w - pw) // 2, y0 + max(bh // 2 - ph // 2, 10 * _S)),
                pt,
                fill=(255, 255, 255),
                font=pf,
            )
    img.save(path, "PNG")


def save_service_pies(all_items, paid_items, path: str | Path, subtitle: str = ""):
    w, h = _CW, _CH
    img, draw = _new(w, h)
    W, H = img.size
    _title(draw, "Tipos de servicio" + (f" · {subtitle}" if subtitle else ""), w)

    def _pie(cy: int, items, title: str):
        cx = W // 2
        r = 220 * _S
        tf = _font(26)
        tw, _ = _text_size(draw, title, tf)
        draw.text((cx - tw // 2, cy - r - 55 * _S), title, fill=TEXT, font=tf)
        if not items:
            msg = "Sin desglose por tipo"
            hint = "(necesita SOAP · toca ↻)"
            mf = _font(24)
            hf = _font(20)
            mw, _ = _text_size(draw, msg, mf)
            hw, _ = _text_size(draw, hint, hf)
            draw.text((cx - mw // 2, cy - 20 * _S), msg, fill=MUTED, font=mf)
            draw.text((cx - hw // 2, cy + 20 * _S), hint, fill=MUTED, font=hf)
            return
        total = sum(v for _, v in items) or 1.0
        ang = -90.0
        for name, val in items:
            sweep = 360.0 * (val / total)
            color = SERVICE_COLORS.get(name, (107, 114, 128))
            if isinstance(color, str):
                color = _hex_to_rgb(color)
            draw.pieslice(
                [cx - r, cy - r, cx + r, cy + r],
                start=ang,
                end=ang + sweep,
                fill=color,
                outline=BG,
            )
            ang += sweep

        legend_y = cy + r + 28 * _S
        lf = _font(22)
        for name, val in items:
            color = SERVICE_COLORS.get(name, (107, 114, 128))
            if isinstance(color, str):
                color = _hex_to_rgb(color)
            short = name.replace(" Services", "")
            line = f"{short}: {_money(val)} ({val / total * 100:.1f}%)"
            draw.ellipse(
                [70 * _S, legend_y + 4 * _S, 94 * _S, legend_y + 28 * _S],
                fill=color,
            )
            draw.text((110 * _S, legend_y), line[:52], fill=MUTED, font=lf)
            legend_y += 40 * _S

    _pie(int(0.30 * H), all_items or [], "Todas (SOAP)")
    _pie(int(0.72 * H), paid_items or [], "Pagadas (SOAP)")
    img.save(path, "PNG")


def save_behavior_monthly(all_months, paid_months, path: str | Path, year: int):
    w, h = _CW, _CH
    img, draw = _new(w, h)
    W, H = img.size
    _title(draw, f"Comportamiento · {year}", w)
    left, right = 90 * _S, W - 50 * _S
    top, bottom = 120 * _S, H - 90 * _S
    draw.rounded_rectangle([left, top, right, bottom], radius=24 * _S, fill=PANEL)

    all_map = dict(all_months or [])
    paid_map = dict(paid_months or [])
    months = list(range(1, 13))
    y_all = [float(all_map.get(m, 0.0)) for m in months]
    y_paid = [float(paid_map.get(m, 0.0)) for m in months]
    vmax = max(y_all + y_paid + [1.0])

    # Escala Y (3 marcas)
    yf = _font(18)
    for frac, label_v in ((0.0, vmax), (0.5, vmax / 2), (1.0, 0.0)):
        yy = top + 50 * _S + frac * (bottom - top - 130 * _S)
        draw.line([(left + 8 * _S, yy), (right - 8 * _S, yy)], fill=GRID, width=_S)
        lab = _money(label_v) if label_v >= 1000 else f"{label_v:,.0f}"
        draw.text((left + 14 * _S, yy - 14 * _S), lab, fill=MUTED, font=yf)

    def _pts(vals):
        pts = []
        for i, v in enumerate(vals):
            x = left + 50 * _S + i * ((right - left - 90 * _S) / 11)
            y = bottom - 70 * _S - (v / vmax) * (bottom - top - 130 * _S)
            pts.append((x, y))
        return pts

    def _polyline(pts, color):
        if len(pts) >= 2:
            draw.line(pts, fill=color, width=6 * _S)
        for x, y in pts:
            draw.ellipse(
                [x - 9 * _S, y - 9 * _S, x + 9 * _S, y + 9 * _S],
                fill=color,
            )

    _polyline(_pts(y_all), BLUE)
    _polyline(_pts(y_paid), TEAL)
    f = _font(20)
    for i, m in enumerate(months):
        x = left + 50 * _S + i * ((right - left - 90 * _S) / 11)
        lab = _MONTHS[m - 1]
        tw, _ = _text_size(draw, lab, f)
        draw.text((x - tw / 2, bottom - 48 * _S), lab, fill=MUTED, font=f)
    lf = _font(24)
    draw.text((left + 20 * _S, top + 16 * _S), "Todas", fill=BLUE, font=lf)
    draw.text((left + 160 * _S, top + 16 * _S), "Pagadas", fill=TEAL, font=lf)
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
    return ordered[-15:], "ultimas actualizaciones"


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
    """Una sola grafica vertical. series: all | paid."""
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
    w, h = _CW, _CH
    img, draw = _new(w, h)
    W, H = img.size
    _title(draw, f"Evolucion PE · {scope}", w, y=18)
    sub = f"{label} · ritmo diario"
    sw, _ = _text_size(draw, sub, _font(22))
    draw.text(((W - sw) // 2, 70 * _S), sub, fill=MUTED, font=_font(22))

    left, right = 90 * _S, W - 45 * _S
    top, bottom = 130 * _S, H - 85 * _S
    draw.rounded_rectangle([left, top, right, bottom], radius=24 * _S, fill=PANEL)

    if not rows:
        draw.text(
            (W // 2 - 100 * _S, H // 2),
            "Sin historial",
            fill=MUTED,
            font=_font(26),
        )
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
            (W // 2 - 180 * _S, H // 2 - 10 * _S),
            "Sin datos en esta serie",
            fill=MUTED,
            font=_font(24),
        )
        img.save(path, "PNG")
        return

    lo, hi, clipped = _useful_ylim(plot_v, pe)
    span = max(hi - lo, 1.0)

    def _xy(i: int, v: float) -> tuple[float, float]:
        if len(plot_d) == 1:
            x = (left + right) / 2
        else:
            x = left + 30 * _S + i * ((right - left - 60 * _S) / (len(plot_d) - 1))
        y = bottom - 55 * _S - ((v - lo) / span) * (bottom - top - 100 * _S)
        return x, y

    # Escala Y
    yf = _font(18)
    for frac, label_v in ((0.0, hi), (0.5, (hi + lo) / 2), (1.0, lo)):
        yy = top + 55 * _S + frac * (bottom - top - 100 * _S)
        draw.line([(left + 8 * _S, yy), (right - 8 * _S, yy)], fill=GRID, width=_S)
        draw.text((left + 14 * _S, yy - 14 * _S), _money(label_v), fill=MUTED, font=yf)

    pe_y = bottom - 55 * _S - ((pe - lo) / span) * (bottom - top - 100 * _S)
    draw.line([(left + 12 * _S, pe_y), (right - 12 * _S, pe_y)], fill=TEAL, width=4 * _S)

    pts = [_xy(i, v) for i, v in enumerate(plot_v)]
    if len(pts) >= 2:
        draw.line(pts, fill=(203, 213, 225), width=6 * _S)
    for (x, y), v in zip(pts, plot_v):
        col = GREEN if v >= pe else RED
        r = 10 * _S
        draw.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=BG)

    f = _font(24)
    draw.text((left + 20 * _S, top + 16 * _S), f"PE {_money(pe)}", fill=TEAL, font=f)
    if clipped:
        draw.text(
            (left + 20 * _S, top + 48 * _S),
            "Escala util (picos ene. fuera)",
            fill=MUTED,
            font=_font(18),
        )

    step = max(1, len(plot_d) // 5)
    df = _font(18)
    for i, d in enumerate(plot_d):
        if i % step != 0 and i != len(plot_d) - 1:
            continue
        x, _ = _xy(i, plot_v[i])
        lab = d.strftime("%d-%b")
        tw, _ = _text_size(draw, lab, df)
        draw.text((x - tw / 2, bottom - 40 * _S), lab, fill=MUTED, font=df)

    last_v = plot_v[-1]
    if lo <= last_v <= hi:
        lx, ly = pts[-1]
        t = _money(last_v)
        draw.text((lx + 12 * _S, ly - 30 * _S), t, fill=TEXT, font=_font(24))

    img.save(path, "PNG")
