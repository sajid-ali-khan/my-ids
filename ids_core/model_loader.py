"""Model and feature loading utilities"""

import joblib
import os


def load_model_and_features(model_dir: str):
    """Load RF model and feature columns from joblib files.
    
    Args:
        model_dir: Path to directory containing model files
        
    Returns:
        tuple: (model, feature_columns)
    """
    model_path = os.path.join(model_dir, 'random_forest_model.pkl')
    columns_path = os.path.join(model_dir, 'model_columns.joblib')
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not os.path.exists(columns_path):
        raise FileNotFoundError(f"Columns file not found: {columns_path}")
    
    model = joblib.load(model_path)
    feature_columns = joblib.load(columns_path)
    
    return model, feature_columns
