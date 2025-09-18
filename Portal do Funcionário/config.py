import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql+psycopg2://postgres:13954@localhost:5432/portal_funcionario')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads')

    SESSION_PERMANENT = False
    
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)