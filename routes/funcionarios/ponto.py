from datetime import datetime, timezone, timedelta
from extensions import db
from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from models import Ferias, Ponto, Marcacao, calcular_horas_ponto
from . import funcionarios_bp

@funcionarios_bp.route('/registrar_ponto', methods=["GET", "POST"])
@login_required
def registrar_ponto():
    hoje = datetime.now(timezone.utc).date()
    agora = datetime.now(timezone.utc).time()

    ferias = Ferias.query.filter(Ferias.funcionario_id == current_user.id, Ferias.status == "aprovado", Ferias.inicio <= hoje, Ferias.fim >= hoje).first()
    if ferias:
        flash("Você está em período de férias. Bom descanso!", "warning")
        return redirect(url_for("funcionarios.dashboard"))
    
    ponto = Ponto.query.filter_by(user_id=current_user.id, data=hoje).first()

    # Verificação de entradas ou saídas existentes
    if not ponto:
        ponto = Ponto(user_id=current_user.id, data=hoje)
        db.session.add(ponto)
        db.session.commit()

    qtd_pontos = Marcacao.query.filter_by(ponto_id=ponto.id).count()

    tipos = ["entrada", "saida_almoco", "retorno_almoco", "saida_final", "extra_inicio", "extra_fim"]

    if qtd_pontos < len(tipos):
        tipo = tipos[qtd_pontos]
        marcacao = Marcacao(data=hoje, hora=agora, tipo=tipo, ponto=ponto)
        db.session.add(marcacao)
        db.session.commit()
        flash(f"{tipo.replace('_',' ').title()} registrada com sucesso!", "success")
    else:
        flash("Você já registrou todos os pontos hoje.", "warning")

    return redirect(url_for("funcionarios.dashboard"))
    
@funcionarios_bp.route('/meus_registros')
@login_required
def meus_registros():
    hoje = datetime.today().date()
    ponto = Ponto.query.filter_by(user_id=current_user.id, data=hoje).first()

    if ponto:
        marcacoes = Marcacao.query.filter_by(ponto_id=ponto.id).order_by(Marcacao.hora).all()
    else:
        marcacoes = []
    
    return render_template("funcionarios/meus_registros.html", ponto=ponto, marcacoes=marcacoes)

@funcionarios_bp.route('/historico')
@login_required
def historico():
    
    hoje = datetime.today().date()
    ano, mes = hoje.year, hoje.month
    inicio = datetime(ano, mes, 1).date()

    registros = Ponto.query.filter(Ponto.user_id == current_user.id, Ponto.data >= inicio).order_by(Ponto.data.asc()).all()
    
    jornada_padrao = timedelta(hours=current_user.empresa.carga_mensal / 22 / 5)

    saldo_total = timedelta()
    extras_total = timedelta()
    deficit_total = timedelta()
    lista = []

    for r in registros:
        marcacoes = Marcacao.query.filter_by(ponto_id=r.id).order_by(Marcacao.hora).all()
        resultado = calcular_horas_ponto(r, carga=jornada_padrao)

        if len(marcacoes) >= 2:
            saldo_total += resultado["saldo"]
            extras_total += resultado["extras"]
            deficit_total += resultado["deficit"] 

        lista.append({
            'data': r.data,
            'entrada': r.marcacoes[0].hora.strftime("%H:%M") if len(marcacoes) > 0 else None,
            'saida_almoco': r.marcacoes[1].hora.strftime("%H:%M") if len(marcacoes) > 1 else None,
            'retorno_almoco': r.marcacoes[2].hora.strftime("%H:%M") if len(marcacoes) > 2 else None,
            'saida': r.marcacoes[-1].hora.strftime("%H:%M") if len(marcacoes) > 3 else None,
            'horas_trabalhadas': resultado['total_trabalhado'],
            'saldo': resultado['saldo'],
            'extras': resultado['extras'],
            'deficit': resultado['deficit']
        })

    return render_template('funcionarios/historico.html', registros=lista, saldo_total=saldo_total, extras_total=extras_total, deficit_total=deficit_total, mes_atual=f"{ano}-{mes:02d}")