# tests/conftest.py
import sys
import os

# Ensure src/ is on sys.path so tests can import packages under src/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
