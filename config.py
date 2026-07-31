"""
Read/write monthly expense for Android.
"""
from __future__ import annotations

from pathlib import Path

import android_paths


def _config_file() -> Path:
    return android_paths.config_path()


def _default_from_conta() -> float:
    try:
        from android_expense import average_expense_last_months

        avg, _ = average_expense_last_months(6)
        if avg is not None:
            return float(avg)
    except Exception:
        pass
    return 7_507.74


def get_monthly_expense(default: float | None = None) -> float:
    if default is None:
        default = _default_from_conta()
    path = _config_file()
    # Migrar config del paquete si aun no hay en storage
    pkg = android_paths.package_dir() / "config.txt"
    if not path.exists() and pkg.exists() and path != pkg:
        try:
            path.write_text(pkg.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            pass
    if not path.exists():
        return default
    try:
        return float(path.read_text(encoding="utf-8").strip())
    except Exception:
        return default


def save_monthly_expense(value: float) -> None:
    try:
        _config_file().write_text(f"{value:.2f}", encoding="utf-8")
    except Exception as exc:
        print("ERROR writing config.txt:", exc)
