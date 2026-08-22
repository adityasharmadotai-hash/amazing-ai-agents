"""Make the project root importable so `from agent import ...` works under
pytest regardless of the invocation directory."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
