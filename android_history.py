"""
Historial PE Android: une seed (PC/conta) + actualizaciones en vivo.
"""
from __future__ import annotations

import json
from pathlib import Path

SEED_PATH = Path(__file__).with_name("data") / "pe_history_seed.json"


def _live_path() -> Path:
    try:
        import android_paths

        return android_paths.live_history_path()
    except Exception:
        return Path("daily_sales_history.json")


def _seed_path() -> Path:
    try:
        import android_paths

        cand = android_paths.seed_data_dir() / "pe_history_seed.json"
        if cand.is_file():
            return cand
    except Exception:
        pass
    return SEED_PATH


def _normalize_entry(e: dict) -> dict | None:
    if not isinstance(e, dict) or not e.get("date"):
        return None
    date = str(e["date"])[:10]
    try:
        all_avg = e.get("all_data_avg")
        paid_avg = e.get("paid_only_avg")
        return {
            "date": date,
            "all_data_avg": float(all_avg) if all_avg is not None else 0.0,
            "paid_only_avg": float(paid_avg) if paid_avg is not None else None,
            "pe_value": float(e["pe_value"]) if e.get("pe_value") is not None else None,
            "pe_value_paid": float(e["pe_value_paid"]) if e.get("pe_value_paid") is not None else None,
            "source": e.get("source") or "live",
        }
    except Exception:
        return None


def load_seed_points() -> list[dict]:
    path = _seed_path()
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    points = raw.get("points") if isinstance(raw, dict) else raw
    if not isinstance(points, list):
        return []
    out = []
    for e in points:
        n = _normalize_entry(e)
        if n:
            out.append(n)
    return out


def load_live_points() -> list[dict]:
    path = _live_path()
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(raw, list):
        return []
    out = []
    for e in raw:
        n = _normalize_entry(e)
        if n:
            n["source"] = n.get("source") or "live"
            out.append(n)
    return out


def available_years(history: list[dict] | None = None) -> list[int]:
    rows = history if history is not None else load_merged_history()
    years = set()
    for e in rows:
        try:
            years.add(int(str(e.get("date"))[:4]))
        except Exception:
            continue
    return sorted(years, reverse=True)


def selectable_years(history: list[dict] | None = None, back: int = 30) -> list[int]:
    from datetime import date

    try:
        from android_year_data import FIRST_DATA_YEAR, conta_available_years
    except Exception:
        FIRST_DATA_YEAR = 2008

        def conta_available_years():
            return []

    today_y = date.today().year
    years = set(available_years(history))
    years.update(conta_available_years())
    if years:
        oldest = min(min(years), FIRST_DATA_YEAR)
    else:
        oldest = max(FIRST_DATA_YEAR, today_y - back + 1)
    for y in range(oldest, today_y + 1):
        years.add(y)
    return sorted(years, reverse=True)


def merge_history(seed: list[dict], live: list[dict]) -> list[dict]:
    by_date: dict[str, dict] = {}
    for e in seed:
        by_date[e["date"]] = dict(e)
    for e in live:
        prev = by_date.get(e["date"])
        merged = dict(e)
        if prev and merged.get("paid_only_avg") is None and prev.get("paid_only_avg") is not None:
            merged["paid_only_avg"] = prev["paid_only_avg"]
        if prev and merged.get("pe_value") is None and prev.get("pe_value") is not None:
            merged["pe_value"] = prev["pe_value"]
            merged["pe_value_paid"] = prev.get("pe_value_paid")
        by_date[e["date"]] = merged
    return [by_date[k] for k in sorted(by_date)]


def load_merged_history() -> list[dict]:
    return merge_history(load_seed_points(), load_live_points())
