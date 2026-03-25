"""Model and feature loading utilities"""

import joblib
import os
import logging

logger = logging.getLogger(__name__)


def load_model_and_features(model_dir: str, use_v2: bool = True):
    """Load RF model and feature columns from joblib files.
    
    Supports v2 model (optimized for real traffic, port features removed)
    with fallback to v1 for backward compatibility.
    
    Args:
        model_dir: Path to directory containing model files
        use_v2: If True, try to load v2 model first. Default: True
        
    Returns:
        tuple: (model, feature_columns, is_v2)
    """
    # Try v2 model (optimized)
    if use_v2:
        model_path_v2 = os.path.join(model_dir, 'random_forest_model_v2.pkl')
        columns_path_v2 = os.path.join(model_dir, 'model_columns_v2.joblib')
        
        if os.path.exists(model_path_v2) and os.path.exists(columns_path_v2):
            try:
                model = joblib.load(model_path_v2)
                feature_columns = joblib.load(columns_path_v2)
                logger.info(f"Loaded v2 model from {model_path_v2}")
                logger.info(f"Features (v2): {len(feature_columns)} columns (port features removed)")
                return model, feature_columns, True
            except Exception as e:
                logger.warning(f"Failed to load v2 model: {e}")
    
    # Fallback to v1 model
    model_path = os.path.join(model_dir, 'random_forest_model.pkl')
    columns_path = os.path.join(model_dir, 'model_columns.joblib')
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not os.path.exists(columns_path):
        raise FileNotFoundError(f"Columns file not found: {columns_path}")
    
    model = joblib.load(model_path)
    feature_columns = joblib.load(columns_path)
    logger.info(f"Loaded v1 model from {model_path}")
    logger.info(f"Features (v1): {len(feature_columns)} columns")
    return model, feature_columns, False


def predict_with_confidence(model, features_aligned):
    """Make prediction with confidence scores.
    
    Args:
        model: Trained RandomForestClassifier
        features_aligned: Aligned feature array [1 x num_features]
        
    Returns:
        tuple: (prediction, confidence, probabilities)
    """
    prediction = model.predict(features_aligned)[0]
    probabilities = model.predict_proba(features_aligned)[0]
    confidence = probabilities.max()
    
    return prediction, confidence, probabilities
