from flask import render_template
from flask_login import login_required
from models import Empresa, User, Ponto
from extensions import db
from utils import superadmin_required
from . import superadmin_bp

@superadmin_bp.route("/dashboard")
@login_required
@superadmin_required
def dashboard():
    total_empresas = Empresa.query.count()
    total_admins = User.query.filter_by(tipo="admin").count()
    total_funcionarios = User.query.filter_by(tipo="funcionario").count()
    total_horas = db.session.query(Ponto).count()
    
    empresas = Empresa.query.all()
    return render_template("superadmin/super_dashboard.html", total_empresas=total_empresas, total_admins=total_admins, total_funcionarios=total_funcionarios, total_horas=total_horas, empresas=empresas)