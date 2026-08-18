import sys
from pathlib import Path

# Add the project root to sys.path so that 'tests' and 'src' are importable
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))
