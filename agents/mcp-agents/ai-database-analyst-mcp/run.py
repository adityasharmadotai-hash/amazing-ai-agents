"""Convenience launcher for the Streamlit app.

Equivalent to ``streamlit run app/main.py`` but also ensures the sample database
exists on first run.

    python run.py
"""

from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def _ensure_sample_db() -> None:
    sample_path = os.path.join(ROOT, "sample_data", "northwind.db")
    if not os.path.exists(sample_path):
        print("Sample database not found — creating it…")
        from scripts.create_sample_db import create_sample_db

        create_sample_db(sample_path)


def main() -> None:
    sys.path.insert(0, ROOT)
    _ensure_sample_db()
    app_path = os.path.join(ROOT, "app", "main.py")
    cmd = [sys.executable, "-m", "streamlit", "run", app_path]
    print("Launching:", " ".join(cmd))
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
