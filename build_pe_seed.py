"""
Genera Version Android/data/pe_history_seed.json
desde data_log (Windows) + gastos conta.

Formato listo para Evolución PE en Android:
  date, all_data_avg, paid_only_avg, pe_value, pe_value_paid, source
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANDROID_DATA = ROOT / "Version Android" / "data"
OUT = ANDROID_DATA / "pe_history_seed.json"
LOG_ALL = ROOT / "data_log_all_data.csv"
LOG_PAID = ROOT / "data_log_only_paid.csv"
GASTOS = ROOT / "Resultados Umbrella" / "gastos_mensuales.json"

sys.path.insert(0, str(ROOT / "Version Android"))
from android_metrics import pe_daily, gross_margin_percent  # noqa: E402


def _read_log(path: Path) -> dict[str, float]:
    """date ISO → AverageDailySales (col 3). Sin cabecera."""
    out: dict[str, float] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            continue
        try:
            dt = datetime.strptime(parts[0][:19], "%Y-%m-%d %H:%M:%S")
            avg = float(parts[2])
        except Exception:
            continue
        # Un punto por día calendario (última actualización del día)
        out[dt.date().isoformat()] = avg
    return out


def _load_gastos() -> dict:
    if not GASTOS.is_file():
        return {}
    raw = json.loads(GASTOS.read_text(encoding="utf-8"))
    return raw.get("months") if isinstance(raw, dict) else {}


def _pe_for_month(months: dict, year: int, month: int, fallback_expense: float) -> float:
    key = f"{year}-{month:02d}"
    rec = months.get(key) if isinstance(months, dict) else None
    if not isinstance(rec, dict):
        # Mes anterior con gasto
        for back in range(1, 13):
            m = month - back
            y = year
            while m <= 0:
                m += 12
                y -= 1
            prev = months.get(f"{y}-{m:02d}")
            if isinstance(prev, dict) and prev.get("expense") is not None:
                rec = prev
                break
    if not isinstance(rec, dict):
        return pe_daily(fallback_expense, 15.0)
    sales = float(rec.get("sales") or 0)
    cost = float(rec.get("cost") or 0)
    expense = float(rec.get("expense") if rec.get("expense") is not None else fallback_expense)
    margin = gross_margin_percent(sales, cost) if sales > 0 else 15.0
    return pe_daily(expense, margin)


def _month_end_points(months: dict, fallback_expense: float) -> list[dict]:
    """Puntos fin de mes desde conta (años/meses con ventas)."""
    import calendar

    rows = []
    for key, rec in sorted(months.items()):
        if not isinstance(rec, dict):
            continue
        try:
            y, m = key.split("-")
            y, m = int(y), int(m)
            last_day = calendar.monthrange(y, m)[1]
            d = date(y, m, last_day)
        except Exception:
            continue
        sales = float(rec.get("sales") or 0)
        if sales <= 0:
            continue
        cost = float(rec.get("cost") or 0)
        expense = float(rec.get("expense") or fallback_expense)
        margin = gross_margin_percent(sales, cost)
        daily = sales / max(last_day, 1)
        pe = pe_daily(expense, margin)
        rows.append(
            {
                "date": d.isoformat(),
                "all_data_avg": round(daily, 2),
                "paid_only_avg": None,  # conta no distingue pagadas
                "pe_value": round(pe, 2),
                "pe_value_paid": round(pe, 2),
                "source": "conta_month",
                "month_sales": round(sales, 2),
            }
        )
    return rows


def build_seed(fallback_expense: float = 7507.74) -> dict:
    all_avg = _read_log(LOG_ALL)
    paid_avg = _read_log(LOG_PAID)
    months = _load_gastos()

    dates = sorted(set(all_avg) | set(paid_avg))
    points = []
    for ds in dates:
        y, m, _ = (int(x) for x in ds.split("-"))
        pe = _pe_for_month(months, y, m, fallback_expense)
        points.append(
            {
                "date": ds,
                "all_data_avg": round(all_avg.get(ds) or 0.0, 2),
                "paid_only_avg": round(paid_avg[ds], 2) if ds in paid_avg else None,
                "pe_value": round(pe, 2),
                "pe_value_paid": round(pe, 2),
                "source": "data_log+conta",
            }
        )

    conta_points = _month_end_points(months, fallback_expense)
    # Conta mensual solo para fechas sin data_log (relleno histórico)
    log_dates = {p["date"] for p in points}
    for cp in conta_points:
        # Evitar solapar el mismo mes si ya hay data_log ese día
        if cp["date"] in log_dates:
            continue
        # Si el mes ya tiene algún punto data_log, no meter fin de mes conta
        ym = cp["date"][:7]
        if any(d.startswith(ym) for d in log_dates):
            continue
        points.append(cp)

    points.sort(key=lambda p: p["date"])
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sources": [
            str(LOG_ALL.name),
            str(LOG_PAID.name),
            str(GASTOS.name),
        ],
        "count": len(points),
        "points": points,
    }


def main():
    ANDROID_DATA.mkdir(parents=True, exist_ok=True)
    seed = build_seed()
    OUT.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK -> {OUT}")
    print(f"Puntos: {seed['count']}")
    if seed["points"]:
        print(f"Desde {seed['points'][0]['date']} hasta {seed['points'][-1]['date']}")
        y2026 = [p for p in seed["points"] if p["date"].startswith("2026")]
        print(f"De 2026: {len(y2026)} puntos")


if __name__ == "__main__":
    main()
