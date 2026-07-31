"""
Datos anuales para Android.
- Año en curso: SOAP (en vivo).
- Años cerrados (desde 2015): conta (gastos_mensuales) para «Todas» = como Windows.
  «Pagadas» sigue por SOAP (si hay) o caché.
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


def conta_year_totals(year: int) -> tuple[float, float, float, list[tuple[int, float]], str] | None:
    """
    (sales, cost, expense_avg, [(mes, sales), ...], note) desde conta.
    None si no hay meses.
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

    sales = cost = 0.0
    expenses = []
    monthly = []
    for m in range(1, 13):
        key = f"{int(year)}-{m:02d}"
        rec = months.get(key)
        if not isinstance(rec, dict):
            continue
        s = float(rec.get("sales") or 0)
        c = float(rec.get("cost") or 0)
        sales += s
        cost += c
        if rec.get("expense") is not None:
            expenses.append(float(rec["expense"]))
        if s > 0:
            monthly.append((m, s))
    if sales <= 0 and not expenses:
        return None
    exp = sum(expenses) / len(expenses) if expenses else 7507.74
    note = f"Conta {year}: {len(monthly)} mes(es) · gasto medio ${exp:,.2f}"
    return sales, cost, round(exp, 2), monthly, note


def metrics_from_conta(year: int) -> tuple[metrics.YearMetrics, list[tuple[int, float]], str] | None:
    packed = conta_year_totals(year)
    if packed is None:
        return None
    sales, cost, exp, monthly, note = packed
    _, _, day_used, days = year_bounds(year)
    m = metrics.compute_year_metrics(
        total_sales=sales,
        total_cost=cost,
        monthly_expense=exp,
        day_of_year=day_used,
        period_days=days,
        days_in_year=days,
    )
    return m, monthly, note
