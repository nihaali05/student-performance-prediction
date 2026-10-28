import os
import secrets

_production = any(
    os.environ.get(name, '').strip().lower() in ('production', 'prod')
    for name in ('APP_ENV', 'FLASK_ENV', 'ENVIRONMENT')
)


def _secret_from_environment(name):
    value = os.environ.get(name)
    if value:
        return value
    if _production:
        raise RuntimeError(f'{name} must be set when running in production.')
    return secrets.token_urlsafe(32)

class Config:
    SECRET_KEY = _secret_from_environment('SECRET_KEY')
    JWT_SECRET_KEY = _secret_from_environment('JWT_SECRET_KEY')
    
    # Dual database support: Use SQLite out-of-the-box, or MySQL if MYSQL_URL is set
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(os.path.dirname(__file__), 'student_analytics.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 MB max upload
