# Enforce UTF-8 I/O in this workspace
# Loaded automatically by Python's site module when project root is on sys.path
import os
import sys

# Prefer Python's UTF-8 mode when available
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Reconfigure standard streams to UTF-8 when supported (Python 3.7+)
try:
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    # Never fail app startup due to console encoding quirks
    pass
