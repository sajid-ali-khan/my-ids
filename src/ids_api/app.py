"""Flask application factory and configuration"""

import os
from flask import Flask, jsonify, render_template
from flask_cors import CORS


def create_app(pipeline):
    """Create and configure Flask application.
    
    Args:
        pipeline: PipelineManager instance
        
    Returns:
        Flask app instance
    """
    # Get the project root directory (parent of ids_api directory)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_folder = os.path.join(project_root, 'web')
    static_folder = os.path.join(project_root, 'web')
    
    # Debug output
    print(f"\n[Flask] Project Root: {project_root}")
    print(f"[Flask] Template Folder: {template_folder} (exists: {os.path.exists(template_folder)})")
    print(f"[Flask] Static Folder: {static_folder} (exists: {os.path.exists(static_folder)})")
    if os.path.exists(static_folder):
        print(f"[Flask] Static Files: {os.listdir(static_folder)}\n")
    
    app = Flask(__name__, 
                template_folder=template_folder, 
                static_folder=static_folder,
                static_url_path='/')
    CORS(app)
    
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
