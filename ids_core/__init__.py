"""IDS Core Module - Pipeline Management"""

from .pipeline import PipelineManager
from .model_loader import load_model_and_features

__all__ = ['PipelineManager', 'load_model_and_features']
