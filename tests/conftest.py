import sys
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.append(str(SRC_PATH))
