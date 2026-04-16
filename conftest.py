"""
Pytest configuration — ensures the project root is on sys.path so that
'from src.rag import ...' style imports work when running pytest from the root.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
