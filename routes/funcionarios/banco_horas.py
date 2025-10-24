from datetime import timedelta
from flask import render_template
from flask_login import current_user, login_required
from models import Ponto, calcular_horas_ponto
from . import funcionarios_bp

@funcionarios_bp.route('/banco_horas_acumulado')
@login_required
def banco_horas_acumulado():
    pontos = Ponto.query.filter(Ponto.user_id == current_user.id).order_by(Ponto.data.asc()).all()

    saldo_total = timedelta()
    extras_total = timedelta()
    deficit_total = timedelta()

    resultados = []

    for ponto in pontos:
        resultado = calcular_horas_ponto(ponto, carga_diaria=timedelta(hours=current_user.empresa.carga_mensal / 22 / 5))
        saldo_total += resultado['saldo']
        extras_total += resultado['extras']
        deficit_total += resultado['deficit']

        resultados.append({
            'data': ponto.data,
            'total_trabalhado': resultado['total_trabalhado'],
            'saldo': resultado['saldo'],
            'extras': resultado['extras'],
            'deficit': resultado['deficit']
        })

    return render_template("funcionarios/banco_horas_acumulado.html", funcionario=current_user,resultados=resultados, saldo_total=saldo_total, extras_total=extras_total, deficit_total=deficit_total)