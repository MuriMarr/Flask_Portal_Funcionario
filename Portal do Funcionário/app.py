import os
from datetime import datetime
from flask import Flask, redirect, url_for
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

    # Blueprints
    from auth import auth_bp
    from admin import admin_bp
    from superadmin import superadmin_bp
    from funcionarios import funcionarios_bp
    from empresas import empresas_bp
    from avisos import avisos_bp

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