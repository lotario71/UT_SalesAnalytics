"""
Read Umbrella-Sales config values.

Currently supports just one line:
    <monthly_expense>   # e.g. 8900.00
"""
from pathlib import Path


CONFIG_FILE = Path(__file__).with_name("config.txt")


def get_monthly_expense(default: float = 8_900.00) -> float:
    """Return the monthly expense saved in config.txt (or the default)."""
    if not CONFIG_FILE.exists():
        return default
    try:
        first_line = CONFIG_FILE.read_text(encoding="utf-8").strip()
        return float(first_line)
    except Exception:
        return default


# ─────────────────────────────────────────────────────────────────────────
# NEW: allow the app to update the value from a settings screen
# ─────────────────────────────────────────────────────────────────────────
def save_monthly_expense(value: float) -> None:
    """Persist a new monthly expense to config.txt."""
    try:
        CONFIG_FILE.write_text(f"{value:.2f}", encoding="utf-8")
    except Exception as exc:
        print("ERROR writing config.txt:", exc)
