from flask import render_template
from flask_login import current_user, login_required
from models import Ponto, Marcacao, calcular_horas_ponto
from collections import defaultdict
from . import funcionarios_bp

@funcionarios_bp.route('/dashboard')
@login_required
def dashboard():
    registros = Ponto.query.filter_by(user_id=current_user.id).all()

    total_trabalhado = sum(
        [calcular_horas_ponto(r)["total_trabalhado"].seconds / 3600 for r in registros], 0
    )

    total_extras = sum(
        [calcular_horas_ponto(r)["extras"].seconds / 3600 for r in registros], 0
    )

    banco_horas = total_trabalhado + total_extras - (current_user.empresa.carga_mensal or 220)
    proximo_pagamento = current_user.salario_mensal

    horas_semanais = defaultdict(float)
    extras_semanais = defaultdict(float)

    for r in registros:
        if r.data:
            semana = r.data.isocalendar()[1]
            resultado = calcular_horas_ponto(r)
            horas_semanais[semana] += resultado["total_trabalhado"].seconds / 3600
            extras_semanais[semana] += resultado["extras"].seconds / 3600
    
    semanas = sorted(horas_semanais.keys())
    horas_semanais_list = [horas_semanais[s] for s in semanas]
    extras_semanais_list = [extras_semanais[s] for s in semanas]

    historico = []
    for r in registros:
        marcacoes = Marcacao.query.filter_by(ponto_id=r.id).order_by(Marcacao.hora).all()
        resultado = calcular_horas_ponto(r)
        horarios = "-".join([m.hora.strftime("%Hh%M") for m in marcacoes])

        historico.append({
            "data": r.data,
            "horarios": horarios,
            "total_trabalhado": resultado["total_trabalhado"],
            "saldo": resultado["saldo"],
            "extras": resultado["extras"],
            "deficit": resultado["deficit"]
        })

    return render_template(
        "funcionarios/funcionario_dashboard.jinja2",
        horas_trabalhadas=round(total_trabalhado, 2),
        horas_extras=round(total_extras, 2),
        banco_horas=round(banco_horas, 2),
        proximo_pagamento=proximo_pagamento,
        semanas=semanas,
        horas_semanais=horas_semanais_list,
        extras_semanais=extras_semanais_list,
        registros=historico
    )