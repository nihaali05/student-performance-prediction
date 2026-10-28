import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from database import db
from seed import seed_database

# Import Blueprints
from routes.auth import auth_bp
from routes.students import students_bp
from routes.faculty import faculty_bp
from routes.attendance_marks import att_marks_bp
from routes.predictions import predictions_bp
from routes.warnings import warnings_bp
from routes.interventions import interventions_bp
from routes.upload import upload_bp
from routes.analytics import analytics_bp
from routes.model_mgmt import model_mgmt_bp
from routes.reports import reports_bp
from routes.study_assistant import study_assistant_bp
from routes.notifications import notifications_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Security fix: replaced wildcard '*' CORS with explicit allowed origins.
    # In production set ALLOWED_ORIGINS env var to your actual domain.
    _allowed_origins = os.environ.get(
        'ALLOWED_ORIGINS',
        'http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000'
    ).split(',')
    CORS(app, resources={r"/api/*": {"origins": _allowed_origins}}, supports_credentials=True)
    
    # Init Database
    db.init_app(app)
    
    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(students_bp, url_prefix='/api/students')
    app.register_blueprint(faculty_bp, url_prefix='/api/faculty')
    app.register_blueprint(att_marks_bp, url_prefix='/api')
    app.register_blueprint(predictions_bp, url_prefix='/api/predictions')
    app.register_blueprint(warnings_bp, url_prefix='/api/warnings')
    app.register_blueprint(interventions_bp, url_prefix='/api/interventions')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(model_mgmt_bp, url_prefix='/api/model')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(study_assistant_bp, url_prefix='/api/study')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'Student Performance Prediction & Early Warning Engine API',
            'version': '1.0.0'
        }), 200
        
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'message': 'Requested API endpoint not found.'}), 404
        
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'message': 'Internal server error occurred.', 'error': str(e)}), 500
        
    # Auto-seed initial DB
    seed_database(app)
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    is_production = os.environ.get('APP_ENV', '').lower() in ('production', 'prod')
    app.run(host='0.0.0.0', port=port, debug=not is_production)
