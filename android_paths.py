"""
Rutas de datos Android vs PC.
En el movil los JSON de lectura van junto al codigo; lo escribible va a storage de la app.
"""
from __future__ import annotations

from pathlib import Path


def package_dir() -> Path:
    return Path(__file__).resolve().parent


def writable_dir() -> Path:
    """Carpeta donde se puede escribir (historial, charts, config)."""
    try:
        from kivy.utils import platform

        if platform == "android":
            from android.storage import app_storage_path

            p = Path(app_storage_path())
            p.mkdir(parents=True, exist_ok=True)
            return p
    except Exception:
        pass
    return package_dir()


def seed_data_dir() -> Path:
    """data/ empaquetado en el APK (conta + seed PE)."""
    return package_dir() / "data"


def chart_path(name: str) -> str:
    return str(writable_dir() / name)


def live_history_path() -> Path:
    return writable_dir() / "daily_sales_history.json"


def config_path() -> Path:
    return writable_dir() / "config.txt"


def activity_log_path() -> Path:
    return writable_dir() / "activity_log.json"
