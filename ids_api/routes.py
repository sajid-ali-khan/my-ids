"""Flask API routes for IDS pipeline"""

from flask import Blueprint, jsonify, current_app, request

api_bp = Blueprint('api', __name__)


# ============================================================================
# CONTROL ENDPOINTS
# ============================================================================

@api_bp.route('/start', methods=['POST'])
def start_pipeline():
    """Start the IDS pipeline.
    
    Returns:
        JSON: {"status": "started", "message": "..."}
    """
    pipeline = current_app.pipeline
    
    if pipeline.is_running:
        return jsonify({
            'status': 'already_running',
            'message': 'Pipeline is already running'
        }), 200
    
    try:
        pipeline.start()
        return jsonify({
            'status': 'started',
            'message': 'Pipeline started successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to start pipeline: {str(e)}'
        }), 500


@api_bp.route('/stop', methods=['POST'])
def stop_pipeline():
    """Stop the IDS pipeline.
    
    Returns:
        JSON: {"status": "stopped", "message": "..."}
    """
    pipeline = current_app.pipeline
    
    if not pipeline.is_running:
        return jsonify({
            'status': 'already_stopped',
            'message': 'Pipeline is not running'
        }), 200
    
    try:
        pipeline.stop()
        return jsonify({
            'status': 'stopped',
            'message': 'Pipeline stopped successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to stop pipeline: {str(e)}'
        }), 500


# ============================================================================
# STATUS & MONITORING ENDPOINTS
# ============================================================================

@api_bp.route('/status', methods=['GET'])
def get_status():
    """Get pipeline status.
    
    Returns:
        JSON: {
            "running": bool,
            "active_flows": int,
            "predictions_processed": int,
            "interface": str
        }
    """
    pipeline = current_app.pipeline
    status = pipeline.get_status()
    
    return jsonify(status), 200


@api_bp.route('/predictions', methods=['GET'])
def get_predictions():
    """Get recent predictions.
    
    Query Parameters:
        - limit (int, optional): Number of predictions to return (default: 50, max: 100)
    
    Returns:
        JSON: {
            "count": int,
            "predictions": [
                {
                    "timestamp": str,
                    "prediction": str,
                    "confidence": float,
                    "src_ip": str,
                    "src_port": int,
                    "dst_ip": str,
                    "dst_port": int,
                    "packets": int
                },
                ...
            ]
        }
    """
    pipeline = current_app.pipeline
    
    # Get limit from query params
    limit = request.args.get('limit', 50, type=int)
    limit = min(limit, 100)  # Cap at 100
    limit = max(limit, 1)    # Min 1
    
    predictions = pipeline.get_predictions(limit=limit)
    
    return jsonify({
        'count': len(predictions),
        'predictions': predictions
    }), 200


@api_bp.route('/flows', methods=['GET'])
def get_flows():
    """Get active flows.
    
    Returns:
        JSON: {
            "active": int,
            "flows": [
                {
                    "src_ip": str,
                    "src_port": int,
                    "dst_ip": str,
                    "dst_port": int,
                    "packets": int,
                    "active_time": float
                },
                ...
            ]
        }
    """
    pipeline = current_app.pipeline
    flows = pipeline.get_active_flows()
    
    return jsonify({
        'active': len(flows),
        'flows': flows
    }), 200


@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get pipeline statistics.
    
    Returns:
        JSON: {
            "total_predictions": int,
            "benign": int,
            "attack_count": int,
            "by_class": {
                "Normal Traffic": int,
                "Bot-Attack": int,
                ...
            }
        }
    """
    pipeline = current_app.pipeline
    stats = pipeline.get_stats()
    
    # Calculate attack count
    attack_count = stats['total'] - stats['benign'] if stats['total'] > 0 else 0
    
    return jsonify({
        'total_predictions': stats['total'],
        'benign': stats['benign'],
        'attack_count': attack_count,
        'by_class': stats['by_class']
    }), 200


@api_bp.route('/summary', methods=['GET'])
def get_summary():
    """Get summary of all key metrics.
    
    Returns:
        JSON: Combined status + stats + recent predictions
    """
    pipeline = current_app.pipeline
    
    status = pipeline.get_status()
    stats = pipeline.get_stats()
    predictions = pipeline.get_predictions(limit=10)
    flows = pipeline.get_active_flows()
    
    attack_count = stats['total'] - stats['benign'] if stats['total'] > 0 else 0
    attack_rate = (attack_count / stats['total'] * 100) if stats['total'] > 0 else 0
    
    return jsonify({
        'pipeline': {
            'running': status['running'],
            'interface': status['interface'],
            'active_flows': status['active_flows']
        },
        'statistics': {
            'total_predictions': stats['total'],
            'benign_traffic': stats['benign'],
            'attack_traffic': attack_count,
            'attack_rate_percent': round(attack_rate, 2),
            'by_class': stats['by_class']
        },
        'recent_predictions': predictions[:5],
        'active_flows_count': len(flows)
    }), 200


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@api_bp.route('/config', methods=['GET'])
def get_config():
    """Get pipeline configuration.
    
    Returns:
        JSON: Configuration details
    """
    pipeline = current_app.pipeline
    
    return jsonify({
        'network_interface': pipeline.network_interface,
        'flusher_interval': pipeline.flusher_interval,
        'idle_timeout': pipeline.idle_timeout,
        'features_count': len(pipeline.feature_columns),
        'max_history': pipeline.max_history
    }), 200


@api_bp.route('/model', methods=['GET'])
def get_model_info():
    """Get model information.
    
    Returns:
        JSON: Model details
    """
    pipeline = current_app.pipeline
    
    # Get class information from stats
    stats = pipeline.get_stats()
    class_names = list(stats['by_class'].keys()) if stats['by_class'] else []
    
    return jsonify({
        'features': len(pipeline.feature_columns),
        'feature_names': pipeline.feature_columns,
        'model_type': str(type(pipeline.model).__name__),
        'classes': class_names
    }), 200
