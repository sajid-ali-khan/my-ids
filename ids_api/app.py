"""Flask application factory and configuration"""

from flask import Flask, jsonify, render_template
from flask_cors import CORS
from ids_core import PipelineManager


def create_app(model_dir: str = './model', interface: str = 'wlp3s0'):
    """Create and configure Flask application.
    
    Args:
        model_dir: Path to model directory
        interface: Network interface to sniff on
        
    Returns:
        Flask app instance
    """
    app = Flask(__name__, template_folder='../web', static_folder='../web')
    CORS(app)
    
    # Initialize PipelineManager
    try:
        pipeline = PipelineManager(
            model_dir=model_dir,
            network_interface=interface,
            flusher_interval=20,
            idle_timeout=30,
            max_history=100
        )
    except Exception as e:
        raise RuntimeError(f"Failed to initialize PipelineManager: {e}")
    
    # Store pipeline in app context for routes to access
    app.pipeline = pipeline
    
    # Register error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # Register blueprints
    from .routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Serve frontend
    @app.route('/')
    def index():
        """Serve dashboard homepage"""
        return render_template('index.html')
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({'status': 'ok'}), 200
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
