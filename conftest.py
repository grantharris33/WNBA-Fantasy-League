import os
import sys
from pathlib import Path

# Add the project root to the Python path so pytest can find the app module
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)
