import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-change')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"mysql+pymysql://{os.environ.get('DB_USER', 'root')}:{os.environ.get('DB_PASSWORD', 'root123')}@{os.environ.get('DB_HOST', '127.0.0.1')}:{os.environ.get('DB_PORT', '3306')}/{os.environ.get('DB_NAME', 'arms_db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 3600,
    }

    UPLOAD_FOLDER = os.environ.get(
        'UPLOAD_FOLDER',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads'),
    )
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
