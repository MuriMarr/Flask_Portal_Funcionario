import os
from datetime import datetime
from flask import Flask, redirect, url_for, session
from flask_login import current_user
from config import Config
from extensions import db, migrate, login_manager
from models import User
from dotenv import load_dotenv
from db_seed import run_seed
from utils import format_timedelta

load_dotenv()
CHAVE_SECRETA_ADMIN = os.environ.get('CHAVE_SECRETA_ADMIN', 'admin@1234')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.cli.add_command(run_seed)
    app.jinja_env.filters['format_timedelta'] = format_timedelta

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @app.before_request
    def refresh_permanent_session():
        if current_user and current_user.is_authenticated:
            session.permanent = True
            session.modified = True

    # Blueprints
    from routes.admin import admin_bp
    from routes.avisos import avisos_bp
    from routes.funcionarios import funcionarios_bp
    from routes.superadmin import superadmin_bp
    from routes.empresas import empresas_bp
    from routes.documentos import documentos_bp
    from auth import auth_bp

    app.register_blueprint(funcionarios_bp, url_prefix='/funcionarios')
    app.register_blueprint(empresas_bp, url_prefix='/empresas')
    app.register_blueprint(avisos_bp, url_prefix='/avisos')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(superadmin_bp, url_prefix='/superadmin')

    @app.route("/")
    def index():
        return redirect(url_for('auth.login'))
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.now}
    
    return app

@login_manager.user_loader
def carregar_usuario(user_id):
    return User.query.get(int(user_id))

# Rodar o app
if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)