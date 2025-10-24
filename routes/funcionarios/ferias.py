from datetime import datetime, timedelta
from extensions import db
from flask import flash, render_template, redirect, request, url_for
from flask_login import current_user, login_required
from models import Ferias
from utils import calcular_saldo_ferias
from . import funcionarios_bp

##### CAMPO PARA FUNÇÕES DE FÉRIAS #####
@funcionarios_bp.route("/ferias")
@login_required
def minhas_ferias():
    saldo = calcular_saldo_ferias(current_user)
    historico = Ferias.query.filter_by(funcionario_id=current_user.id).order_by(Ferias.inicio.desc()).all()
    return render_template("funcionarios/ferias.html", saldo=saldo, historico=historico)

@funcionarios_bp.route('/ferias/solicitar', methods=['GET', 'POST'])
@login_required
def solicitar_ferias():
    if request.method == "POST":
        inicio = request.form.get("inicio")
        fim = request.form.get("fim")

        if not inicio or not fim:
            flash("Por favor, preencha todas as datas.", "warning")
            return redirect(url_for("funcionarios.solicitar_ferias"))
        
        inicio = datetime.strptime(inicio, "%Y-%m-%d").date()
        fim = datetime.strptime(fim, "%Y-%m-%d").date()
        dias = (fim - inicio).days + 1

        saldo = calcular_saldo_ferias(current_user)

        if dias > saldo:
            flash("Você não possui saldo suficiente de férias.", "danger")
            return redirect(url_for("funcionarios.solicitar_ferias"))
        
        nova_ferias = Ferias(funcionario_id=current_user.id, inicio=inicio, fim=fim, dias=dias, status="pendente")
        db.session.add(nova_ferias)
        db.session.commit()
        flash("Solicitação de férias enviada com sucesso!", "success")
        return redirect(url_for("funcionarios.minhas_ferias"))
    
    return render_template("funcionarios/solicitar_ferias.html")