"""
Métricas año en curso (SOAP) alineadas con cuadrantes Windows básicos.
Sin conta: gasto = config (respaldo).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

SERVICE_TYPE_NAMES = {
    1: "Hotel Services",
    2: "Transfer Services",
    4: "Tour Services",
    8: "Miscellaneous Services",
    16: "Car Services",
    32: "Flight Services",
}


def pe_daily(expense_monthly: float, gross_profit_percent: float) -> float:
    if not gross_profit_percent or float(gross_profit_percent) <= 0:
        return 0.0
    return (float(expense_monthly) / (float(gross_profit_percent) / 100.0)) / 30.0


def gross_margin_percent(total_sales: float, total_cost: float) -> float:
    sales = float(total_sales or 0)
    cost = float(total_cost or 0)
    if sales <= 0:
        return 0.0
    return round((1.0 - cost / sales) * 100.0, 2)


def money(v: float) -> str:
    sign = "-" if v < 0 else ""
    return f"{sign}${abs(float(v)):,.2f}"


def money_card(v: float) -> str:
    """Formato corto para tarjetas móviles (evita que se corte el total)."""
    n = float(v or 0)
    sign = "-" if n < 0 else ""
    av = abs(n)
    if av >= 1_000_000:
        return f"{sign}${av / 1_000_000:.2f}M"
    if av >= 10_000:
        return f"{sign}${av:,.0f}"
    return f"{sign}${av:,.2f}"


def pct(v: float) -> str:
    return f"{float(v):.2f}%"


@dataclass(frozen=True)
class YearMetrics:
    total_sales: float
    total_cost: float
    day_of_year: int
    period_days: int
    daily_avg: float
    margin_pct: float
    breakeven: float
    sales_needed: float
    vs_pe: float
    predicted_sales: float
    gross_profit_est: float
    expenses_year: float
    net_est: float
    net_margin_pct: float
    monthly_expense: float
    # True = año cerrado: neto/gastos/bruto oficiales de conta (como Windows).
    official_accounting: bool = False

    @property
    def vs_pe_ok(self) -> bool:
        return self.vs_pe >= 0

    @property
    def net_ok(self) -> bool:
        return self.net_est >= 0

    @property
    def sales_ok(self) -> bool:
        return self.total_sales >= self.sales_needed

    @property
    def daily_ok(self) -> bool:
        return self.daily_avg >= self.breakeven


def compute_year_metrics(
    *,
    total_sales: float,
    total_cost: float,
    monthly_expense: float,
    day_of_year: int,
    period_days: int = 365,
    days_in_year: int = 365,
    official_accounting: bool = False,
    official_gross: float | None = None,
    official_expenses: float | None = None,
    official_net: float | None = None,
) -> YearMetrics:
    sales = float(total_sales or 0)
    cost = float(total_cost or 0)
    expense = float(monthly_expense or 0)
    day = max(int(day_of_year or 1), 1)
    p_days = max(int(period_days or 365), 1)
    year_days = max(int(days_in_year or 365), 1)

    if sales <= 0:
        expenses_y = (
            float(official_expenses)
            if official_accounting and official_expenses is not None
            else expense * 12.0
        )
        net0 = (
            float(official_net)
            if official_accounting and official_net is not None
            else -expenses_y
        )
        return YearMetrics(
            total_sales=0.0,
            total_cost=0.0,
            day_of_year=day,
            period_days=p_days,
            daily_avg=0.0,
            margin_pct=0.0,
            breakeven=0.0,
            sales_needed=0.0,
            vs_pe=0.0,
            predicted_sales=0.0,
            gross_profit_est=float(official_gross or 0.0),
            expenses_year=expenses_y,
            net_est=net0,
            net_margin_pct=0.0,
            monthly_expense=expense,
            official_accounting=bool(official_accounting),
        )

    daily = sales / day
    margin = gross_margin_percent(sales, cost)
    pe = pe_daily(expense, margin)
    needed = pe * p_days

    if official_accounting:
        # Periodo cerrado: sin proyección lineal; cifras oficiales de conta.
        predicted = sales
        gross_est = (
            float(official_gross)
            if official_gross is not None
            else round(sales - cost, 2)
        )
        expenses_y = (
            float(official_expenses)
            if official_expenses is not None
            else expense * 12.0
        )
        net = (
            float(official_net)
            if official_net is not None
            else round(gross_est - expenses_y, 2)
        )
        net_m = (net / sales) * 100.0 if sales else 0.0
    else:
        predicted = daily * year_days
        gross_est = predicted * (margin / 100.0)
        expenses_y = expense * 12.0
        net = gross_est - expenses_y
        net_m = (net / predicted) * 100.0 if predicted else 0.0

    return YearMetrics(
        total_sales=sales,
        total_cost=cost,
        day_of_year=day,
        period_days=p_days,
        daily_avg=daily,
        margin_pct=margin,
        breakeven=pe,
        sales_needed=needed,
        vs_pe=daily - pe,
        predicted_sales=predicted,
        gross_profit_est=gross_est,
        expenses_year=expenses_y,
        net_est=net,
        net_margin_pct=net_m,
        monthly_expense=expense,
        official_accounting=bool(official_accounting),
    )


def cards_payload(m: YearMetrics) -> dict[str, dict]:
    """Datos para tarjetas estilo Windows (título, líneas, tono, popup estructurado)."""
    if m.official_accounting:
        net_title = "Resultado neto (conta)"
        net_line2 = "Oficial conta · sin proyección"
    else:
        net_title = "Resultado neto est."
        net_line2 = f"Proy. {money(m.predicted_sales)}"
    return {
        "sales": {
            "title": "Ventas (real vs PE)",
            "line1": f"Real {money_card(m.total_sales)}",
            "line2": f"Nec. {money_card(m.sales_needed)}",
            "tone1": "bad" if not m.sales_ok else "ok",
            "tone2": None,
            "popup": _popup_sales(m),
        },
        "margin": {
            "title": "Márgenes %",
            "line1": f"Bruto {pct(m.margin_pct)}",
            "line2": f"Neto {pct(m.net_margin_pct)}",
            "tone1": None,
            "tone2": "ok" if m.net_ok else "bad",
            "popup": _popup_margin(m),
        },
        "daily": {
            "title": "Media diaria (real vs PE)",
            "line1": f"Real {money_card(m.daily_avg)}",
            "line2": f"Nec. {money_card(m.breakeven)}",
            "tone1": "bad" if not m.daily_ok else "ok",
            "tone2": None,
            "popup": _popup_daily(m),
        },
        "pe": {
            "title": "Punto de equilibrio",
            "line1": money_card(m.breakeven),
            "line2": f"Gasto {money_card(m.monthly_expense)}",
            "tone1": None,
            "tone2": None,
            "popup": _popup_pe(m),
        },
        "vs_pe": {
            "title": "Vs punto de equilibrio",
            "line1": money_card(m.vs_pe),
            "line2": "Media − PE diario",
            "tone1": "ok" if m.vs_pe_ok else "bad",
            "tone2": None,
            "popup": _popup_vs_pe(m),
        },
        "net": {
            "title": net_title,
            "line1": money_card(m.net_est),
            "line2": net_line2 if m.official_accounting else f"Proy. {money_card(m.predicted_sales)}",
            "tone1": "ok" if m.net_ok else "bad",
            "tone2": None,
            "popup": _popup_net(m),
        },
    }


def _popup(
    *,
    badge: str | None,
    badge_tone: str | None,
    rows: list[dict],
    formula: str = "",
    footer: str = "",
) -> dict:
    return {
        "badge": badge,
        "badge_tone": badge_tone,
        "rows": rows,
        "formula": formula,
        "footer": footer,
    }


def _popup_sales(m: YearMetrics) -> dict:
    footer = (
        "Fuente: contabilidad (año cerrado)."
        if m.official_accounting
        else "Fuente: SOAP (SQL Umbrella). Año en curso."
    )
    return _popup(
        badge="Sobre objetivo" if m.sales_ok else "Bajo objetivo",
        badge_tone="ok" if m.sales_ok else "bad",
        rows=[
            {"label": "Ventas reales", "value": money(m.total_sales), "tone": "ok" if m.sales_ok else "bad"},
            {"label": "Necesario PE (año)", "value": money(m.sales_needed), "tone": None},
            {
                "label": "Hueco",
                "value": money(m.total_sales - m.sales_needed),
                "tone": "ok" if m.sales_ok else "bad",
            },
        ],
        formula=f"Necesario = PE diario × {m.period_days} días\n= {money(m.breakeven)} × {m.period_days}",
        footer=footer,
    )


def _popup_daily(m: YearMetrics) -> dict:
    return _popup(
        badge="Sobre PE" if m.daily_ok else "Bajo PE",
        badge_tone="ok" if m.daily_ok else "bad",
        rows=[
            {"label": "Media diaria", "value": money(m.daily_avg), "tone": "ok" if m.daily_ok else "bad"},
            {"label": "PE diario", "value": money(m.breakeven), "tone": None},
            {"label": "Ventas totales", "value": money(m.total_sales), "tone": None},
            {"label": "Días usados", "value": str(m.day_of_year), "tone": None},
        ],
        formula=f"Media = Ventas ÷ días\n{money(m.total_sales)} ÷ {m.day_of_year} = {money(m.daily_avg)}",
        footer=f"Periodo calendario: {m.period_days} días.",
    )


def _popup_pe(m: YearMetrics) -> dict:
    return _popup(
        badge="PE diario",
        badge_tone=None,
        rows=[
            {"label": "PE diario", "value": money(m.breakeven), "tone": None},
            {"label": "Gasto mensual", "value": money(m.monthly_expense), "tone": None},
            {"label": "Margen bruto", "value": pct(m.margin_pct), "tone": None},
        ],
        formula=(
            "PE = (Gasto ÷ margen) ÷ 30\n"
            f"({money(m.monthly_expense)} ÷ {m.margin_pct / 100:.4f}) ÷ 30 = {money(m.breakeven)}"
        ),
        footer="Gasto desde config (media conta 6 meses o valor editado).",
    )


def _popup_vs_pe(m: YearMetrics) -> dict:
    return _popup(
        badge="Sobre PE" if m.vs_pe_ok else "Bajo PE",
        badge_tone="ok" if m.vs_pe_ok else "bad",
        rows=[
            {"label": "Diff. vs PE", "value": money(m.vs_pe), "tone": "ok" if m.vs_pe_ok else "bad"},
            {"label": "Media diaria", "value": money(m.daily_avg), "tone": None},
            {"label": "PE diario", "value": money(m.breakeven), "tone": None},
        ],
        formula=f"Diff = Media − PE\n{money(m.daily_avg)} − {money(m.breakeven)} = {money(m.vs_pe)}",
    )


def _popup_margin(m: YearMetrics) -> dict:
    gross = m.gross_profit_est if m.official_accounting else (m.total_sales - m.total_cost)
    if m.official_accounting:
        formula = (
            "Margen bruto % = (Ventas − Coste) ÷ Ventas × 100\n"
            f"= {money(gross)} ÷ {money(m.total_sales)} × 100 = {pct(m.margin_pct)}\n\n"
            "Margen neto % = Neto conta ÷ Ventas × 100\n"
            f"= {money(m.net_est)} ÷ {money(m.total_sales)} × 100 = {pct(m.net_margin_pct)}"
        )
        footer = "Año cerrado: sin proyección; neto oficial de estados de resultado."
        net_label = "Margen neto (conta)"
        rows = [
            {"label": "Ventas", "value": money(m.total_sales), "tone": None},
            {"label": "Coste", "value": money(m.total_cost), "tone": None},
            {"label": "Ganancia bruta", "value": money(gross), "tone": None},
            {"label": "Margen bruto", "value": pct(m.margin_pct), "tone": None},
            {"label": "Resultado neto (conta)", "value": money(m.net_est), "tone": "ok" if m.net_ok else "bad"},
            {"label": net_label, "value": pct(m.net_margin_pct), "tone": "ok" if m.net_ok else "bad"},
        ]
    else:
        formula = (
            "Margen bruto % = (Ventas − Coste) ÷ Ventas × 100\n"
            f"= ({money(m.total_sales)} − {money(m.total_cost)}) ÷ {money(m.total_sales)} × 100 "
            f"= {pct(m.margin_pct)}\n\n"
            "Margen neto % = Neto est. ÷ Proyección ventas × 100\n"
            f"= {money(m.net_est)} ÷ {money(m.predicted_sales)} × 100 = {pct(m.net_margin_pct)}"
        )
        footer = "Año en curso: neto estimado con proyección lineal."
        rows = [
            {"label": "Ventas", "value": money(m.total_sales), "tone": None},
            {"label": "Coste", "value": money(m.total_cost), "tone": None},
            {"label": "Ganancia bruta", "value": money(m.total_sales - m.total_cost), "tone": None},
            {"label": "Margen bruto", "value": pct(m.margin_pct), "tone": None},
            {"label": "Proyección ventas", "value": money(m.predicted_sales), "tone": None},
            {"label": "Neto estimado", "value": money(m.net_est), "tone": "ok" if m.net_ok else "bad"},
            {"label": "Margen neto est.", "value": pct(m.net_margin_pct), "tone": "ok" if m.net_ok else "bad"},
        ]
    return _popup(
        badge="Neto positivo" if m.net_ok else "Neto negativo",
        badge_tone="ok" if m.net_ok else "bad",
        rows=rows,
        formula=formula,
        footer=footer,
    )


def _popup_net(m: YearMetrics) -> dict:
    if m.official_accounting:
        return _popup(
            badge="Beneficio conta" if m.net_ok else "Pérdida conta",
            badge_tone="ok" if m.net_ok else "bad",
            rows=[
                {"label": "Neto (conta)", "value": money(m.net_est), "tone": "ok" if m.net_ok else "bad"},
                {"label": "Ventas", "value": money(m.total_sales), "tone": None},
                {"label": "Ganancia bruta", "value": money(m.gross_profit_est), "tone": None},
                {"label": "Gastos año (conta)", "value": money(m.expenses_year), "tone": None},
                {"label": "Margen neto", "value": pct(m.net_margin_pct), "tone": "ok" if m.net_ok else "bad"},
            ],
            formula=(
                "Método CONTABILIDAD (año cerrado)\n"
                "Neto = suma mensual de estados (bruto − gastos + otros ingresos).\n"
                "Sin proyección lineal ni SOAP."
            ),
            footer="Misma regla que Windows en periodos cerrados.",
        )
    return _popup(
        badge="Beneficio" if m.net_ok else "Pérdida",
        badge_tone="ok" if m.net_ok else "bad",
        rows=[
            {"label": "Neto estimado", "value": money(m.net_est), "tone": "ok" if m.net_ok else "bad"},
            {"label": "Proyección ventas", "value": money(m.predicted_sales), "tone": None},
            {"label": "Ganancia bruta est.", "value": money(m.gross_profit_est), "tone": None},
            {"label": "Gastos año", "value": money(m.expenses_year), "tone": None},
        ],
        formula=(
            "Método LINEAL (Android · año en curso)\n"
            f"Proy. = media × 365 = {money(m.predicted_sales)}\n"
            f"Neto = bruto − gastos ({money(m.expenses_year)})"
        ),
    )


def _rows(data) -> list[dict]:
    """Acepta lista de dicts (Android) u objeto tipo DataFrame legacy."""
    if data is None:
        return []
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    # Compatibilidad por si llega un DataFrame en PC
    if hasattr(data, "to_dict") and hasattr(data, "empty"):
        if getattr(data, "empty", True):
            return []
        return data.to_dict(orient="records")
    return []


def sum_column(data, candidates: tuple[str, ...]) -> float:
    rows = _rows(data)
    if not rows:
        return 0.0
    for col in candidates:
        total = 0.0
        found = False
        for r in rows:
            if col not in r or r[col] in (None, ""):
                continue
            found = True
            try:
                total += float(r[col])
            except Exception:
                pass
        if found:
            return total
    return 0.0


def prepare_sales_df(data):
    """Normaliza tipos y nombres de servicio. Devuelve list[dict]."""
    rows = _rows(data)
    out: list[dict] = []
    for raw in rows:
        r = dict(raw)
        for col in ("TotalPrice", "TotalCost"):
            if col in r and r[col] not in (None, ""):
                try:
                    r[col] = float(r[col])
                except Exception:
                    r[col] = 0.0
        if "ServiceType" in r and r["ServiceType"] not in (None, ""):
            try:
                st = int(float(r["ServiceType"]))
                r["ServiceType"] = st
                r["ServiceTypeName"] = SERVICE_TYPE_NAMES.get(st, "Other")
            except Exception:
                r["ServiceTypeName"] = "Other"
        for col in ("GroupByMonth", "GroupByYear"):
            if col in r and r[col] not in (None, ""):
                try:
                    r[col] = int(float(r[col]))
                except Exception:
                    pass
        out.append(r)
    return out


def monthly_sales(data) -> list[tuple[int, float]]:
    """[(mes, ventas), ...]"""
    rows = _rows(data)
    if not rows:
        return []
    totals: dict[int, float] = {}
    for r in rows:
        if "GroupByMonth" not in r:
            continue
        try:
            m = int(r["GroupByMonth"])
            v = float(r.get("TotalPrice") or 0)
        except Exception:
            continue
        totals[m] = totals.get(m, 0.0) + v
    return sorted(totals.items())


def service_sales(data) -> list[tuple[str, float]]:
    rows = _rows(data)
    if not rows:
        return []
    totals: dict[str, float] = {}
    for r in rows:
        name = r.get("ServiceTypeName") or "Other"
        try:
            v = float(r.get("TotalPrice") or 0)
        except Exception:
            v = 0.0
        totals[str(name)] = totals.get(str(name), 0.0) + v
    return sorted(totals.items(), key=lambda x: x[1], reverse=True)


SALES_COLS = ("TotalPrice", "TotalSales", "Total", "SalesTotal", "Importe")
COST_COLS = ("TotalCost", "Cost", "TotalCosts")
