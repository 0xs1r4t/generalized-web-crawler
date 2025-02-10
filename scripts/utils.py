import os
import sys
from pathlib import Path


def setup_project_path():
    """Add project root to Python path"""
    project_root = str(Path(__file__).parent.parent)
    sys.path.append(project_root)
