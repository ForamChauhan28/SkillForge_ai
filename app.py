import os
from flask import Flask, render_template_string, request, jsonify
from config import Config
from models.db import init_database


def create_app():
    """Application factory for SkillForge AI."""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

    # Ensure upload folder exists
    upload_path = os.path.join(app.root_path, Config.UPLOAD_FOLDER)
    os.makedirs(upload_path, exist_ok=True)

    # Initialize database
    try:
        init_database()
    except Exception as e:
        print(f"[WARNING] Database init warning: {e}")
        print("Make sure MySQL is running and properly configured!")

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.roadmap_routes import roadmap_bp
    from routes.api_routes import api_bp
    from routes.analytics_routes import analytics_bp
    from routes.chat_routes import chat_bp
    from routes.mock_interview_routes import mock_interview_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(roadmap_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(analytics_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(mock_interview_bp)

    # ── Error Handlers ──
    @app.errorhandler(500)
    def internal_error(error):
        # Return JSON for API/AJAX requests
        if (request.path.startswith('/api/') or
            request.is_json or
            request.headers.get('Accept', '').startswith('application/json') or
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'):
            return jsonify({'success': False, 'error': 'Internal server error. Please try again.'}), 500
        return render_template_string("""
        <!DOCTYPE html><html><head><title>Server Error</title>
        <style>body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;
        min-height:100vh;background:#0f0f23;color:#fff;text-align:center;}
        .box{padding:3rem;border-radius:1rem;background:#1a1a3e;max-width:500px;}
        h1{font-size:3rem;margin-bottom:0.5rem;} a{color:#7c3aed;}</style></head>
        <body><div class="box"><h1>⚡ 500</h1><p>Something went wrong on our end.</p>
        <p>Please check that the database is connected.</p>
        <a href="/">← Back to Home</a></div></body></html>
        """), 500

    @app.errorhandler(404)
    def not_found(error):
        if (request.path.startswith('/api/') or
            request.is_json or
            request.headers.get('Accept', '').startswith('application/json')):
            return jsonify({'success': False, 'error': 'Not found'}), 404
        return render_template_string("""
        <!DOCTYPE html><html><head><title>Not Found</title>
        <style>body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;
        min-height:100vh;background:#0f0f23;color:#fff;text-align:center;}
        .box{padding:3rem;border-radius:1rem;background:#1a1a3e;max-width:500px;}
        h1{font-size:3rem;margin-bottom:0.5rem;} a{color:#7c3aed;}</style></head>
        <body><div class="box"><h1>⚡ 404</h1><p>Page not found.</p>
        <a href="/">← Back to Home</a></div></body></html>
        """), 404

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
