"""
Gasto mensual para Android.
Prioridad: media últimos N meses con conta (gastos_mensuales.json) → config.txt.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

# Candidatos: data local (APK/seed) y carpeta Windows de desarrollo
def _candidates():
    try:
        import android_paths

        yield android_paths.seed_data_dir() / "gastos_mensuales.json"
    except Exception:
        pass
    yield Path(__file__).with_name("data") / "gastos_mensuales.json"
    yield Path(__file__).resolve().parent.parent / "Resultados Umbrella" / "gastos_mensuales.json"


def find_expense_store_path() -> Path | None:
    for p in _candidates():
        if p.is_file() and p.stat().st_size > 0:
            return p
    return None


def load_monthly_expenses() -> list[tuple[str, float]]:
    """[(YYYY-MM, expense), ...] ordenado ascendente, solo meses con gasto."""
    path = find_expense_store_path()
    if path is None:
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    months = raw.get("months") if isinstance(raw, dict) else None
    if not isinstance(months, dict):
        return []
    out = []
    today = date.today()
    for key, rec in months.items():
        if not isinstance(rec, dict) or rec.get("expense") is None:
            continue
        try:
            y, m = key.split("-")
            y, m = int(y), int(m)
            if date(y, m, 1) > today:
                continue
            out.append((key, float(rec["expense"])))
        except Exception:
            continue
    out.sort(key=lambda x: x[0])
    return out


def average_expense_last_months(n: int = 6) -> tuple[float | None, str]:
    """
    Media de los últimos N meses con gasto contable.
    Devuelve (media, nota explicativa).
    """
    rows = load_monthly_expenses()
    if not rows:
        return None, "Sin archivo de gastos conta (gastos_mensuales.json)."
    last = rows[-max(n, 1) :]
    avg = sum(v for _, v in last) / len(last)
    labels = ", ".join(k for k, _ in last)
    note = (
        f"Media de {len(last)} mes(es) conta: {labels}\n"
        f"Promedio: ${avg:,.2f}"
    )
    return round(avg, 2), note


def average_expense_for_year(year: int) -> tuple[float | None, str]:
    """Media de gasto conta de un año concreto (meses con dato)."""
    rows = [(k, v) for k, v in load_monthly_expenses() if k.startswith(f"{int(year)}-")]
    if not rows:
        return None, f"Sin gastos conta en {year}."
    avg = sum(v for _, v in rows) / len(rows)
    note = f"Media conta {year}: {len(rows)} mes(es) · ${avg:,.2f}"
    return round(avg, 2), note


def resolve_monthly_expense(year: int | None = None) -> tuple[float, str]:
    """
    Gasto a usar en el dashboard.
    Año pasado → media conta de ese año si existe.
    Año actual → config (o media 6 meses).
    """
    y = int(year or date.today().year)
    if y < date.today().year:
        avg, note = average_expense_for_year(y)
        if avg is not None:
            return avg, note
    cfg = None
    try:
        import config

        cfg = float(config.get_monthly_expense())
    except Exception:
        cfg = None
    if cfg is not None:
        return cfg, "Gasto desde config (respaldo móvil)."
    avg6, note6 = average_expense_last_months(6)
    if avg6 is not None:
        return avg6, note6
    return 7507.74, "Gasto por defecto."
