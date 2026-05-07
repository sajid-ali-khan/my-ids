"""Flask API routes for IDS pipeline"""

from flask import Blueprint, jsonify, current_app, request
from .dns_utils import get_hostname

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
    
    # Add domain names for source and destination IPs
    for pred in predictions:
        pred['src_domain'] = get_hostname(pred.get('src_ip', ''))
        pred['dst_domain'] = get_hostname(pred.get('dst_ip', ''))
    
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
    
    # Add domain names for source and destination IPs
    for flow in flows:
        flow['src_domain'] = get_hostname(flow.get('src_ip', ''))
        flow['dst_domain'] = get_hostname(flow.get('dst_ip', ''))
    
    return jsonify({
        'active': len(flows),
        'flows': flows
    }), 200


@api_bp.route('/aggregation-windows', methods=['GET'])
def get_aggregation_windows():
    """Get active flow aggregation windows for brute force detection.
    
    Returns:
        JSON: {
            "active_windows": int,
            "windows": [
                {
                    "src_ip": str,
                    "dst_ip": str,
                    "dst_port": int,
                    "flow_count": int,
                    "window_age_seconds": float,
                    "aggregate_features": {
                        "flow_count": float,
                        "avg_duration": float,
                        "avg_packet_count": float,
                        "avg_bytes": float,
                        "fin_ratio": float,
                        "rst_ratio": float,
                        "connection_rate": float,
                        ...
                    }
                },
                ...
            ]
        }
    """
    pipeline = current_app.pipeline
    windows = pipeline.get_aggregation_windows()
    
    # Add domain names for IPs
    for window in windows:
        window['src_domain'] = get_hostname(window.get('src_ip', ''))
        window['dst_domain'] = get_hostname(window.get('dst_ip', ''))
    
    return jsonify({
        'active_windows': len(windows),
        'windows': windows
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
    
    # Add domain names to predictions
    for pred in predictions:
        pred['src_domain'] = get_hostname(pred.get('src_ip', ''))
        pred['dst_domain'] = get_hostname(pred.get('dst_ip', ''))
    
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

@api_bp.route('/config', methods=['GET', 'POST'])
def manage_config():
    """Get or update pipeline configuration.
    
    GET Returns:
        JSON: Configuration details
        
    POST Parameters (JSON):
        - flusher_interval (int, optional): Interval for flusher thread in seconds
        - idle_timeout (int, optional): Timeout for idle flows in seconds
        - max_history (int, optional): Maximum prediction history size
        
    POST Returns:
        JSON: Updated configuration
    """
    from ids_cli.config import ConfigManager
    
    pipeline = current_app.pipeline
    
    if request.method == 'GET':
        # Return current configuration
        return jsonify({
            'network_interface': pipeline.network_interface,
            'flusher_interval': pipeline.flusher_interval,
            'idle_timeout': pipeline.idle_timeout,
            'max_history': pipeline.max_history,
            'features_count': len(pipeline.feature_columns),
            'model_type': str(type(pipeline.model).__name__)
        }), 200
    
    elif request.method == 'POST':
        # Update configuration
        try:
            data = request.get_json()
            
            updates = {}
            
            # Validate and extract flusher_interval
            if 'flusher_interval' in data:
                flusher_interval = int(data['flusher_interval'])
                if flusher_interval <= 0:
                    return jsonify({'error': 'flusher_interval must be > 0'}), 400
                updates['flusher_interval'] = flusher_interval
                pipeline.flusher_interval = flusher_interval
            
            # Validate and extract idle_timeout
            if 'idle_timeout' in data:
                idle_timeout = int(data['idle_timeout'])
                if idle_timeout <= 0:
                    return jsonify({'error': 'idle_timeout must be > 0'}), 400
                updates['idle_timeout'] = idle_timeout
                pipeline.idle_timeout = idle_timeout
            
            # Validate and extract max_history
            if 'max_history' in data:
                max_history = int(data['max_history'])
                if max_history <= 0:
                    return jsonify({'error': 'max_history must be > 0'}), 400
                updates['max_history'] = max_history
                pipeline.max_history = max_history
            
            # Save to config file
            if updates:
                if ConfigManager.update(updates):
                    return jsonify({
                        'status': 'success',
                        'message': 'Configuration updated successfully',
                        'config': {
                            'flusher_interval': pipeline.flusher_interval,
                            'idle_timeout': pipeline.idle_timeout,
                            'max_history': pipeline.max_history
                        }
                    }), 200
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Failed to save configuration'
                    }), 500
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'No valid configuration parameters provided'
                }), 400
        
        except (ValueError, TypeError) as e:
            return jsonify({
                'status': 'error',
                'message': f'Invalid parameter format: {str(e)}'
            }), 400
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error updating configuration: {str(e)}'
            }), 500


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


# ============================================================================
# PERSISTENT ALERTS - SQLite Database
# ============================================================================

@api_bp.route('/persistent-alerts', methods=['GET'])
def get_persistent_alerts():
    """Get persistent alerts from SQLite database.
    
    Query parameters:
        - limit (int, optional): Max alerts to return (default: 50, max: 500)
        - severity (str, optional): Filter by severity (critical, high, medium, low)
        - attack_type (str, optional): Filter by attack type
        - offset (int, optional): Number of alerts to skip
    
    Returns:
        JSON: {
            "total": int,
            "alerts": [alert_record, ...]
        }
    """
    pipeline = current_app.pipeline
    
    if not pipeline.db_enabled:
        return jsonify({
            'error': 'Database not enabled',
            'alerts': []
        }), 503
    
    limit = request.args.get('limit', 50, type=int)
    limit = min(limit, 500)  # Cap at 500
    limit = max(limit, 1)
    
    severity = request.args.get('severity', None, type=str)
    attack_type = request.args.get('attack_type', None, type=str)
    
    alerts = pipeline.get_persistent_alerts(limit=limit, severity=severity, attack_type=attack_type)
    
    return jsonify({
        'total': len(alerts),
        'alerts': alerts
    }), 200


@api_bp.route('/alert-stats', methods=['GET'])
def get_alert_statistics():
    """Get statistics about persistent alerts.
    
    Returns:
        JSON: {
            "total_alerts": int,
            "by_severity": {severity: count, ...},
            "by_attack_type": {attack_type: count, ...},
            "critical_count": int,
            "high_count": int,
            "acknowledged_count": int,
            "today_count": int
        }
    """
    pipeline = current_app.pipeline
    
    if not pipeline.db_enabled:
        return jsonify({
            'error': 'Database not enabled',
            'total_alerts': 0
        }), 503
    
    stats = pipeline.get_persistent_alert_stats()
    
    return jsonify(stats), 200
