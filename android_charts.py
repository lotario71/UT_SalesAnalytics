"""Graficas Pillow verticales — tipografia tipo Vs pagadas, ancho completo, sin overflow."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (10, 14, 22)
PANEL = (22, 30, 42)
TITLEBAR = (28, 40, 58)
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

_CW, _CH = 1080, 1680
_S = 2
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


def _money(n: float) -> str:
    return f"${n:,.0f}"


def _title_bar(draw, w: int, text: str, y: int = 10) -> int:
    bar_h = 58
    W = w * _S
    draw.rounded_rectangle(
        [10 * _S, y * _S, W - 10 * _S, (y + bar_h) * _S],
        radius=14 * _S,
        fill=TITLEBAR,
    )
    f = _font(32)
    tw, th = _text_size(draw, text, f)
    draw.text(
        ((W - tw) // 2, y * _S + (bar_h * _S - th) // 2),
        text,
        fill=TEXT,
        font=f,
    )
    return y + bar_h


def save_vs_paid(all_total: float, paid_total: float, path: str | Path, subtitle: str = ""):
    w, h = _CW, _CH
    img, draw = _new(w, h)
    W, H = img.size
    title = "Todas vs pagadas" + (f" · {subtitle}" if subtitle else "")
    bar_bottom = _title_bar(draw, w, title, y=12)

    # Casi borde a borde
    left, right = 20 * _S, W - 20 * _S
    top = (bar_bottom + 14) * _S
    bottom = H - 70 * _S
    draw.rounded_rectangle([left, top, right, bottom], radius=22 * _S, fill=PANEL)

    values = [float(all_total or 0), float(paid_total or 0)]
    vmax = max(values + [1.0])
    labels = ["Todas", "Pagadas"]
    colors = [BLUE, TEAL]
    # Barras anchas aprovechando todo el panel
    bar_w = 340 * _S
    gap = 80 * _S
    total_w = bar_w * 2 + gap
    base_x = (left + right - total_w) // 2
    chart_top = top + 95 * _S
    chart_bottom = bottom - 65 * _S
    usable = chart_bottom - chart_top
    for i, (lab, val, col) in enumerate(zip(labels, values, colors)):
        x0 = base_x + i * (bar_w + gap)
        bh = int((val / vmax) * usable * 0.92)
        y0 = chart_bottom - bh
        draw.rounded_rectangle([x0, y0, x0 + bar_w, chart_bottom], radius=16 * _S, fill=col)
        f = _font(36)
        t = _money(val)
        tw, _ = _text_size(draw, t, f)
        draw.text((x0 + (bar_w - tw) // 2, y0 - 58 * _S), t, fill=TEXT, font=f)
        f2 = _font(30)
        lw, _ = _text_size(draw, lab, f2)
        draw.text((x0 + (bar_w - lw) // 2, chart_bottom + 16 * _S), lab, fill=MUTED, font=f2)
        if i == 1 and values[0] > 0:
            pct = values[1] / values[0] * 100
            pt = f"{pct:.1f}%"
            pf = _font(40)
            pw, ph = _text_size(draw, pt, pf)
            draw.text(
                (x0 + (bar_w - pw) // 2, y0 + max(bh // 2 - ph // 2, 8 * _S)),
                pt,
                fill=(255, 255, 255),
                font=pf,
            )
    img.save(path, "PNG")


def save_service_pie(
    items,
    path: str | Path,
    *,
    title: str,
    hint: str = "",
    subtitle: str = "",
):
    w, h = _CW, _CH
    img, draw = _new(w, h)
    W, H = img.size

    if hint:
        hf = _font(24)
        tw, th = _text_size(draw, hint, hf)
        px = (W - tw) // 2 - 28 * _S
        draw.rounded_rectangle(
            [px, 14 * _S, px + tw + 56 * _S, 14 * _S + th + 24 * _S],
            radius=18 * _S,
            fill=(40, 55, 75),
        )
        draw.text((px + 28 * _S, 24 * _S), hint, fill=TEAL, font=hf)
        y0 = 68
    else:
        y0 = 16

    ttl = title + (f" · {subtitle}" if subtitle else "")
    tf = _font(32)
    tw, _ = _text_size(draw, ttl, tf)
    draw.text(((W - tw) // 2, y0 * _S), ttl, fill=TEXT, font=tf)

    cx = W // 2
    cy = int(0.40 * H)
    r = 360 * _S  # mas grande
    if not items:
        msg = "Sin desglose por tipo"
        hint2 = "(necesita SOAP · toca refresh)"
        mf = _font(28)
        hf2 = _font(22)
        mw, _ = _text_size(draw, msg, mf)
        hw, _ = _text_size(draw, hint2, hf2)
        draw.text((cx - mw // 2, cy - 20 * _S), msg, fill=MUTED, font=mf)
        draw.text((cx - hw // 2, cy + 30 * _S), hint2, fill=MUTED, font=hf2)
        img.save(path, "PNG")
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
    lf = _font(30)  # leyenda grande como Vs
    for name, val in items:
        color = SERVICE_COLORS.get(name, (107, 114, 128))
        if isinstance(color, str):
            color = _hex_to_rgb(color)
        short = name.replace(" Services", "")
        line = f"{short}: {_money(val)} ({val / total * 100:.1f}%)"
        draw.ellipse(
            [50 * _S, legend_y + 2 * _S, 100 * _S, legend_y + 52 * _S],
            fill=color,
        )
        draw.text((120 * _S, legend_y + 8 * _S), line[:48], fill=TEXT, font=lf)
        legend_y += 62 * _S
    img.save(path, "PNG")


def save_service_pies(all_items, paid_items, path: str | Path, subtitle: str = ""):
    path = Path(path)
    stem = path.stem
    if stem.startswith("chart_tipos_") and not stem.startswith("chart_tipos_paid_"):
        paid_path = path.with_name(stem.replace("chart_tipos_", "chart_tipos_paid_", 1) + path.suffix)
    else:
        paid_path = path.with_name(path.stem + "_paid" + path.suffix)
    save_service_pie(
        all_items or [],
        path,
        title="Todas (SOAP)",
        hint="Todas  ·  desliza > Pagadas",
        subtitle=subtitle,
    )
    save_service_pie(
        paid_items or [],
        paid_path,
        title="Pagadas (SOAP)",
        hint="< Todas  ·  Pagadas",
        subtitle=subtitle,
    )
    return str(path), str(paid_path)


def save_behavior_monthly(all_months, paid_months, path: str | Path, year: int):
    w, h = _CW, _CH
    img, draw = _new(w, h)
    W, H = img.size
    bar_bottom = _title_bar(draw, w, f"Comportamiento · {year}", y=10)

    left, right = 12 * _S, W - 12 * _S
    panel_top = (bar_bottom + 10) * _S
    bottom = H - 55 * _S
    draw.rounded_rectangle([left, panel_top, right, bottom], radius=22 * _S, fill=PANEL)

    leg_y = panel_top + 16 * _S
    lf = _font(30)
    draw.text((left + 20 * _S, leg_y), "Todas", fill=BLUE, font=lf)
    draw.text((left + 200 * _S, leg_y), "Pagadas", fill=TEAL, font=lf)

    # Margen izquierdo para escala Y grande
    plot_l = left + 150 * _S
    plot_r = right - 20 * _S
    chart_top = leg_y + 55 * _S
    chart_bottom = bottom - 70 * _S

    all_map = dict(all_months or [])
    paid_map = dict(paid_months or [])
    months = list(range(1, 13))
    y_all = [float(all_map.get(m, 0.0)) for m in months]
    y_paid = [float(paid_map.get(m, 0.0)) for m in months]
    vmax = max(y_all + y_paid + [1.0])

    yf = _font(26)
    for i in range(5):
        frac = i / 4
        yy = chart_top + frac * (chart_bottom - chart_top)
        val = vmax * (1 - frac)
        draw.line([(plot_l, yy), (plot_r, yy)], fill=GRID, width=2 * _S)
        lab = _money(val)
        tw, th = _text_size(draw, lab, yf)
        draw.text((plot_l - tw - 12 * _S, yy - th // 2), lab, fill=MUTED, font=yf)

    def _pts(vals):
        pts = []
        for i, v in enumerate(vals):
            x = plot_l + 10 * _S + i * ((plot_r - plot_l - 20 * _S) / 11)
            y = chart_bottom - (v / vmax) * (chart_bottom - chart_top)
            # clamp dentro del panel
            y = max(chart_top + 8 * _S, min(chart_bottom - 8 * _S, y))
            pts.append((x, y))
        return pts

    def _polyline(pts, color):
        if len(pts) >= 2:
            draw.line(pts, fill=color, width=8 * _S)
        for x, y in pts:
            draw.ellipse([x - 12 * _S, y - 12 * _S, x + 12 * _S, y + 12 * _S], fill=color)

    _polyline(_pts(y_all), BLUE)
    _polyline(_pts(y_paid), TEAL)
    f = _font(24)
    for i, m in enumerate(months):
        x = plot_l + 10 * _S + i * ((plot_r - plot_l - 20 * _S) / 11)
        lab = _MONTHS[m - 1]
        tw, _ = _text_size(draw, lab, f)
        draw.text((x - tw / 2, chart_bottom + 18 * _S), lab, fill=MUTED, font=f)
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
    bar_bottom = _title_bar(draw, w, f"Evolucion PE · {scope}", y=10)

    sub = f"{label} · ritmo diario"
    sw, _ = _text_size(draw, sub, _font(26))
    draw.text(((W - sw) // 2, (bar_bottom + 10) * _S), sub, fill=MUTED, font=_font(26))

    pe_row = bar_bottom + 46
    draw.text((24 * _S, pe_row * _S), f"PE {_money(pe)}", fill=TEAL, font=_font(30))

    left, right = 12 * _S, W - 12 * _S
    # Panel EMPIEZA debajo de titulo/subtitulo/PE — la curva no puede salir de aqui
    panel_top = (pe_row + 48) * _S
    bottom = H - 55 * _S
    draw.rounded_rectangle([left, panel_top, right, bottom], radius=22 * _S, fill=PANEL)

    if not rows:
        draw.text((W // 2 - 100 * _S, H // 2), "Sin historial", fill=MUTED, font=_font(28))
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
            (W // 2 - 180 * _S, H // 2),
            "Sin datos en esta serie",
            fill=MUTED,
            font=_font(26),
        )
        img.save(path, "PNG")
        return

    lo, hi, clipped = _useful_ylim(plot_v, pe)
    span = max(hi - lo, 1.0)

    plot_l = left + 150 * _S
    plot_r = right - 20 * _S
    # Padding interno para que puntos/lineas no toquen el borde ni el titulo
    pad = 28 * _S
    chart_top = panel_top + pad
    chart_bottom = bottom - 75 * _S
    dot_r = 12 * _S

    def _xy(i: int, v: float) -> tuple[float, float]:
        if len(plot_d) == 1:
            x = (plot_l + plot_r) / 2
        else:
            x = plot_l + 10 * _S + i * ((plot_r - plot_l - 20 * _S) / (len(plot_d) - 1))
        # Clamp valor a escala y punto dentro del panel
        vv = max(lo, min(hi, v))
        y = chart_bottom - ((vv - lo) / span) * (chart_bottom - chart_top)
        y = max(chart_top + dot_r, min(chart_bottom - dot_r, y))
        return x, y

    yf = _font(26)
    for i in range(5):
        frac = i / 4
        yy = chart_top + frac * (chart_bottom - chart_top)
        val = hi - frac * (hi - lo)
        draw.line([(plot_l, yy), (plot_r, yy)], fill=GRID, width=2 * _S)
        lab = _money(val)
        tw, th = _text_size(draw, lab, yf)
        draw.text((plot_l - tw - 12 * _S, yy - th // 2), lab, fill=MUTED, font=yf)

    pe_clamped = max(lo, min(hi, pe))
    pe_y = chart_bottom - ((pe_clamped - lo) / span) * (chart_bottom - chart_top)
    pe_y = max(chart_top + 4 * _S, min(chart_bottom - 4 * _S, pe_y))
    draw.line([(plot_l, pe_y), (plot_r, pe_y)], fill=TEAL, width=5 * _S)

    if clipped:
        draw.text(
            (plot_l + 8 * _S, chart_top + 4 * _S),
            "Escala util (picos fuera)",
            fill=MUTED,
            font=_font(18),
        )

    pts = [_xy(i, v) for i, v in enumerate(plot_v)]
    if len(pts) >= 2:
        draw.line(pts, fill=(203, 213, 225), width=8 * _S)
    for (x, y), v in zip(pts, plot_v):
        col = GREEN if v >= pe else RED
        draw.ellipse([x - dot_r, y - dot_r, x + dot_r, y + dot_r], fill=col, outline=BG)

    df = _font(24)
    step = max(1, len(plot_d) // 5)
    for i, d in enumerate(plot_d):
        if i % step != 0 and i != len(plot_d) - 1:
            continue
        x, _ = _xy(i, plot_v[i])
        lab = d.strftime("%d-%b")
        tw, _ = _text_size(draw, lab, df)
        draw.text((x - tw / 2, chart_bottom + 16 * _S), lab, fill=MUTED, font=df)

    last_v = plot_v[-1]
    if lo <= last_v <= hi:
        lx, ly = pts[-1]
        t = _money(last_v)
        tw, th = _text_size(draw, t, _font(28))
        # etiqueta dentro del panel
        tx = max(plot_l + 4 * _S, min(lx - tw - 8 * _S, plot_r - tw - 4 * _S))
        ty = max(chart_top + 4 * _S, ly - th - 8 * _S)
        draw.text((tx, ty), t, fill=TEXT, font=_font(28))

    img.save(path, "PNG")
