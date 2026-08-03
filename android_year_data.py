"""
Datos anuales para Android.
- Año en curso: SOAP (en vivo).
- Años cerrados: conta (gastos_mensuales) para «Todas», neto oficial como Windows.
  «Solo pagadas» no aplica (se oculta / N/D).
"""
from __future__ import annotations

import calendar
from datetime import date

import android_expense as expense
import android_metrics as metrics

FIRST_DATA_YEAR = 2008  # primer año con conta en gastos_mensuales


def conta_available_years() -> list[int]:
    """Años con al menos un mes en conta (sales o expense)."""
    path = expense.find_expense_store_path()
    if path is None:
        return []
    import json

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    months = raw.get("months") if isinstance(raw, dict) else None
    if not isinstance(months, dict):
        return []
    years = set()
    for key, rec in months.items():
        if not isinstance(rec, dict):
            continue
        if rec.get("sales") is None and rec.get("expense") is None:
            continue
        try:
            years.add(int(str(key)[:4]))
        except Exception:
            continue
    return sorted(years)


def year_bounds(year: int) -> tuple[date, date, int, int]:
    """(first, last, day_of_year_usado, days_in_year)."""
    today = date.today()
    y = int(year)
    first = date(y, 1, 1)
    last = date(y, 12, 31)
    days = 366 if calendar.isleap(y) else 365
    if y == today.year:
        used = today.timetuple().tm_yday
    elif y < today.year:
        used = days
    else:
        used = 1
    return first, last, used, days


def _net_from_month_record(rec: dict) -> float:
    """Misma regla que Windows: neto Excel si existe; si no, bruto − gastos + otros."""
    if rec.get("net") is not None:
        try:
            return float(rec["net"])
        except Exception:
            pass
    sales = float(rec.get("sales") or 0)
    cost = float(rec.get("cost") or 0)
    gross = rec.get("gross_profit")
    gross = float(gross) if gross is not None else (sales - cost)
    expense_m = float(rec.get("expense") or 0)
    other_income = float(rec.get("other_income") or 0)
    return round(gross - expense_m + other_income, 2)


def conta_year_pl(year: int) -> dict | None:
    """
    Resumen P&L del año desde conta (meses con sales).
    Claves: sales, cost, gross, expense_total, expense_avg, net, other_income,
    monthly [(mes, sales), ...], months_count, note.
    """
    path = expense.find_expense_store_path()
    if path is None:
        return None
    import json

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    months = raw.get("months") if isinstance(raw, dict) else None
    if not isinstance(months, dict):
        return None

    sales = cost = gross = expense_total = other_income = net = 0.0
    expenses_for_avg: list[float] = []
    monthly: list[tuple[int, float]] = []
    months_count = 0

    for m in range(1, 13):
        key = f"{int(year)}-{m:02d}"
        rec = months.get(key)
        if not isinstance(rec, dict):
            continue
        if rec.get("sales") is None:
            continue
        s = float(rec.get("sales") or 0)
        c = float(rec.get("cost") or 0)
        g = rec.get("gross_profit")
        g = float(g) if g is not None else (s - c)
        e = float(rec.get("expense") or 0)
        oi = float(rec.get("other_income") or 0)
        sales += s
        cost += c
        gross += g
        expense_total += e
        other_income += oi
        net += _net_from_month_record(rec)
        months_count += 1
        if rec.get("expense") is not None:
            expenses_for_avg.append(e)
        if s > 0:
            monthly.append((m, s))

    if months_count == 0:
        return None

    exp_avg = (
        sum(expenses_for_avg) / len(expenses_for_avg)
        if expenses_for_avg
        else (expense_total / months_count if months_count else 7507.74)
    )
    note = (
        f"Conta {year}: {months_count} mes(es) · "
        f"neto oficial ${net:,.2f} · gasto medio ${exp_avg:,.2f}"
    )
    return {
        "sales": round(sales, 2),
        "cost": round(cost, 2),
        "gross": round(gross, 2),
        "expense_total": round(expense_total, 2),
        "expense_avg": round(exp_avg, 2),
        "net": round(net, 2),
        "other_income": round(other_income, 2),
        "monthly": monthly,
        "months_count": months_count,
        "note": note,
    }


def conta_year_totals(year: int) -> tuple[float, float, float, list[tuple[int, float]], str] | None:
    """Compat: (sales, cost, expense_avg, monthly, note)."""
    pl = conta_year_pl(year)
    if pl is None:
        return None
    return pl["sales"], pl["cost"], pl["expense_avg"], pl["monthly"], pl["note"]


def metrics_from_conta(year: int) -> tuple[metrics.YearMetrics, list[tuple[int, float]], str] | None:
    """Año cerrado: ventas/coste/PE desde conta; neto = oficial (sin proyección lineal)."""
    pl = conta_year_pl(year)
    if pl is None:
        return None
    _, _, day_used, days = year_bounds(year)
    m = metrics.compute_year_metrics(
        total_sales=pl["sales"],
        total_cost=pl["cost"],
        monthly_expense=pl["expense_avg"],
        day_of_year=day_used,
        period_days=days,
        days_in_year=days,
        official_accounting=True,
        official_gross=pl["gross"],
        official_expenses=pl["expense_total"],
        official_net=pl["net"],
    )
    return m, pl["monthly"], pl["note"]
