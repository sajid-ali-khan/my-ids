"""IDS Core Module - Pipeline Management"""

# Ensure project root is in path for pipx installations
import sys
from pathlib import Path
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from .pipeline import PipelineManager
from .model_loader import load_model_and_features

__all__ = ['PipelineManager', 'load_model_and_features']
