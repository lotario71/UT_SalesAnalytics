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
) -> YearMetrics:
    sales = float(total_sales or 0)
    cost = float(total_cost or 0)
    expense = float(monthly_expense or 0)
    day = max(int(day_of_year or 1), 1)
    p_days = max(int(period_days or 365), 1)
    year_days = max(int(days_in_year or 365), 1)

    if sales <= 0:
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
            gross_profit_est=0.0,
            expenses_year=expense * 12.0,
            net_est=-expense * 12.0,
            net_margin_pct=0.0,
            monthly_expense=expense,
        )

    daily = sales / day
    margin = gross_margin_percent(sales, cost)
    pe = pe_daily(expense, margin)
    needed = pe * p_days
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
    )


def cards_payload(m: YearMetrics) -> dict[str, dict]:
    """Datos para tarjetas estilo Windows (título, líneas, tono, popup estructurado)."""
    return {
        "sales": {
            "title": "Ventas (real vs PE)",
            "line1": f"Real {money(m.total_sales)}",
            "line2": f"Necesario {money(m.sales_needed)}",
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
            "line1": f"Real {money(m.daily_avg)}",
            "line2": f"Necesario {money(m.breakeven)}",
            "tone1": "bad" if not m.daily_ok else "ok",
            "tone2": None,
            "popup": _popup_daily(m),
        },
        "pe": {
            "title": "Punto de equilibrio",
            "line1": money(m.breakeven),
            "line2": f"Gasto mes {money(m.monthly_expense)}",
            "tone1": None,
            "tone2": None,
            "popup": _popup_pe(m),
        },
        "vs_pe": {
            "title": "Vs punto de equilibrio",
            "line1": money(m.vs_pe),
            "line2": "Media − PE diario",
            "tone1": "ok" if m.vs_pe_ok else "bad",
            "tone2": None,
            "popup": _popup_vs_pe(m),
        },
        "net": {
            "title": "Resultado neto est.",
            "line1": money(m.net_est),
            "line2": f"Proy. {money(m.predicted_sales)}",
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
        footer="Fuente: SOAP (SQL Umbrella). Sin conta en Android.",
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
    return _popup(
        badge="Neto positivo" if m.net_ok else "Neto negativo",
        badge_tone="ok" if m.net_ok else "bad",
        rows=[
            {"label": "Margen bruto", "value": pct(m.margin_pct), "tone": None},
            {"label": "Margen neto est.", "value": pct(m.net_margin_pct), "tone": "ok" if m.net_ok else "bad"},
            {"label": "Ventas", "value": money(m.total_sales), "tone": None},
            {"label": "Coste", "value": money(m.total_cost), "tone": None},
        ],
        formula=(
            "Bruto = (1 − coste/ventas) × 100\n"
            f"Neto % = Neto ÷ proyección × 100\n"
            f"Neto {money(m.net_est)} · Proy. {money(m.predicted_sales)}"
        ),
    )


def _popup_net(m: YearMetrics) -> dict:
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
            "Método LINEAL (Android)\n"
            f"Proy. = media × 365 = {money(m.predicted_sales)}\n"
            f"Neto = bruto − gastos ({money(m.expenses_year)})"
        ),
    )


def sum_column(df, candidates: tuple[str, ...]) -> float:
    if df is None or getattr(df, "empty", True):
        return 0.0
    for col in candidates:
        if col in df.columns:
            try:
                return float(df[col].astype(float).sum())
            except Exception:
                return 0.0
    return 0.0


def prepare_sales_df(df):
    """Normaliza tipos y nombres de servicio."""
    if df is None or getattr(df, "empty", True):
        return df
    out = df.copy()
    for col in ("TotalPrice", "TotalCost"):
        if col in out.columns:
            out[col] = out[col].astype(float)
    if "ServiceType" in out.columns:
        out["ServiceType"] = out["ServiceType"].astype(int)
        out["ServiceTypeName"] = out["ServiceType"].map(SERVICE_TYPE_NAMES).fillna("Other")
    if "GroupByMonth" in out.columns:
        out["GroupByMonth"] = out["GroupByMonth"].astype(int)
    if "GroupByYear" in out.columns:
        out["GroupByYear"] = out["GroupByYear"].astype(int)
    return out


def monthly_sales(df) -> list[tuple[int, float]]:
    """[(mes, ventas), ...] para el año del DF."""
    if df is None or getattr(df, "empty", True) or "GroupByMonth" not in df.columns:
        return []
    g = df.groupby("GroupByMonth")["TotalPrice"].sum().sort_index()
    return [(int(m), float(v)) for m, v in g.items()]


def service_sales(df) -> list[tuple[str, float]]:
    if df is None or getattr(df, "empty", True):
        return []
    if "ServiceTypeName" not in df.columns:
        return []
    g = df.groupby("ServiceTypeName")["TotalPrice"].sum().sort_values(ascending=False)
    return [(str(k), float(v)) for k, v in g.items()]


SALES_COLS = ("TotalPrice", "TotalSales", "Total", "SalesTotal", "Importe")
COST_COLS = ("TotalCost", "Cost", "TotalCosts")
