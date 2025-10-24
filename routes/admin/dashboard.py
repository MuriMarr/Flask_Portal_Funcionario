from flask import render_template
from flask_login import current_user, login_required
from datetime import datetime, timedelta
from models import User, Ponto, Marcacao
from utils import admin_required
from . import admin_bp

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    funcionarios = User.query.filter_by(empresa_id=current_user.empresa_id, tipo="funcionario").all()
    total_funcionarios = len(funcionarios)

    registros = Ponto.query.join(User).filter(User.empresa_id == current_user.empresa_id).all()
    total_registros = len(registros)

    total_horas = timedelta()
    pendentes = []

    for r in registros:
        marcacoes = Marcacao.query.filter_by(ponto_id=r.id).order_by(Marcacao.hora).all()
        if len(marcacoes) >= 2:
            entrada = datetime.combine(r.data, marcacoes[0].hora)
            saida = datetime.combine(r.data, marcacoes[-1].hora)
            total_horas += (saida - entrada)        
        elif len(marcacoes) == 1:
            pendentes.append(r) 
            
    return render_template('admin/admin_dashboard.html', total_funcionarios=total_funcionarios, total_registros=total_registros, total_horas=total_horas, pendentes=pendentes)