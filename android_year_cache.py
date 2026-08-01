"""
Cache local del ultimo año SOAP/conta cargado.
Permite reabrir la app con los mismos numeros (no solo conta empaquetada).
"""
from __future__ import annotations

import json
from dataclasses import asdict, fields
from datetime import datetime
from pathlib import Path
from typing import Any

import android_metrics as metrics
import android_paths as apaths


def _cache_path(year: int) -> Path:
    return apaths.writable_dir() / f"year_cache_{int(year)}.json"


def _metrics_to_dict(m: metrics.YearMetrics) -> dict:
    return asdict(m)


def _metrics_from_dict(d: dict | None) -> metrics.YearMetrics | None:
    if not d or not isinstance(d, dict):
        return None
    names = {f.name for f in fields(metrics.YearMetrics)}
    payload = {k: d[k] for k in names if k in d}
    try:
        return metrics.YearMetrics(**payload)
    except Exception:
        return None


def save_year_bundle(year: int, bundle: dict) -> None:
    """Persiste metricas + series (sin objetos Python vivos)."""
    m_all = bundle.get("m_all")
    m_paid = bundle.get("m_paid")
    if m_all is None:
        return
    payload: dict[str, Any] = {
        "year": int(year),
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "source_note": bundle.get("source_note") or "",
        "m_all": _metrics_to_dict(m_all),
        "m_paid": _metrics_to_dict(m_paid or m_all),
        "monthly_all": list(bundle.get("monthly_all") or []),
        "monthly_paid": list(bundle.get("monthly_paid") or []),
        "services_all": list(bundle.get("services_all") or []),
        "services_paid": list(bundle.get("services_paid") or []),
        "closed": bool(bundle.get("closed")),
        "paid_pending": False,
        "from_network": True,
    }
    path = _cache_path(year)
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def load_year_bundle(year: int) -> dict | None:
    path = _cache_path(year)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(raw, dict):
        return None
    m_all = _metrics_from_dict(raw.get("m_all"))
    m_paid = _metrics_from_dict(raw.get("m_paid")) or m_all
    if m_all is None:
        return None
    saved = raw.get("saved_at") or ""
    note = raw.get("source_note") or "SOAP local"
    if saved:
        note = f"{note} · guardado {saved}"
    return {
        "m_all": m_all,
        "m_paid": m_paid,
        "monthly_all": [tuple(x) if isinstance(x, list) else x for x in (raw.get("monthly_all") or [])],
        "monthly_paid": [tuple(x) if isinstance(x, list) else x for x in (raw.get("monthly_paid") or [])],
        "services_all": [tuple(x) if isinstance(x, list) else x for x in (raw.get("services_all") or [])],
        "services_paid": [tuple(x) if isinstance(x, list) else x for x in (raw.get("services_paid") or [])],
        "source_note": note,
        "closed": bool(raw.get("closed")),
        "paid_pending": False,
        "from_disk": True,
        "saved_at": saved,
    }


def clear_year_bundle(year: int) -> None:
    path = _cache_path(year)
    try:
        if path.exists():
            path.unlink()
    except Exception:
        pass
