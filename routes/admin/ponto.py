from datetime import date, datetime, timedelta, timezone
from extensions import db
from flask import flash, redirect, url_for, render_template
from flask_login import current_user, login_required
from models import User, Ponto, Marcacao, calcular_horas_ponto
from utils import admin_required
from . import admin_bp

# Registro de ponto para administradores
@admin_bp.route('/registrar_ponto', methods=["GET", "POST"])
@login_required
def registrar_ponto():
    hoje = datetime.now(timezone.utc).date()
    agora = datetime.now(timezone.utc).time()

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

    return redirect(url_for("admin.dashboard"))

@admin_bp.route('/banco_horas/mensal/<int:usuario_id>')
@login_required
def banco_horas_mensal(usuario_id):
    funcionario = User.query.get_or_404(usuario_id)

    hoje = datetime.today().date()
    inicio_mes = date(hoje.year, hoje.month, 1)

    pontos = (
        Ponto.query
        .filter(Ponto.usuario_id == usuario_id, Ponto.data >= inicio_mes)
        .order_by(Ponto.data.asc())
        .all()
    )

    saldo_total = timedelta()
    extras_total = timedelta()
    deficit_total = timedelta()

    resultados = []

    for ponto in pontos:
        resultado = calcular_horas_ponto(ponto, carga_diaria=timedelta(hours=8))

        saldo_total += resultado["saldo"]
        extras_total += resultado["extras"]
        deficit_total += resultado["deficit"]

        resultados.append({
            "data": ponto.data,
            "total_trabalhado": resultado["total_trabalhado"],
            "saldo": resultado["saldo"],
            "extras": resultado["extras"],
            "deficit": resultado["deficit"],
        })

    return render_template(
        "admin/banco_horas_mensal.html",
        funcionario=funcionario,
        resultados=resultados,
        saldo_total=saldo_total,
        extras_total=extras_total,
        deficit_total=deficit_total
    )

@admin_bp.route('/banco_horas/acumulado/<int:usuario_id>')
@login_required
def banco_horas_acumulado(usuario_id):
    funcionario = User.query.get_or_404(usuario_id)

    pontos = (
        Ponto.query
        .filter(Ponto.usuario_id == usuario_id)
        .order_by(Ponto.data.asc())
        .all()
    )

    saldo_total = timedelta()
    extras_total = timedelta()
    deficit_total = timedelta()

    resultados = []

    for ponto in pontos:
        resultado = calcular_horas_ponto(ponto, carga_diaria=timedelta(hours=8))

        saldo_total += resultado["saldo"]
        extras_total += resultado["extras"]
        deficit_total += resultado["deficit"]

        resultados.append({
            "data": ponto.data,
            "total_trabalhado": resultado["total_trabalhado"],
            "saldo": resultado["saldo"],
            "extras": resultado["extras"],
            "deficit": resultado["deficit"],
        })

    return render_template(
        "admin/banco_horas_acumulado.html",
        funcionario=funcionario,
        resultados=resultados,
        saldo_total=saldo_total,
        extras_total=extras_total,
        deficit_total=deficit_total
    )

@admin_bp.route('/funcionario/<int:id>/historico')
@login_required
@admin_required
def historico_funcionario(id):
    funcionario = User.query.get_or_404(id)
    
    hoje = datetime.today().date()
    ano, mes = hoje.year, hoje.month
    inicio = datetime(ano, mes, 1).date()
    
    registros = Ponto.query.filter(Ponto.user_id == id, Ponto.data >= inicio).order_by(Ponto.data.asc()).all()

    jornada_padrao = timedelta(hours=funcionario.empresa.carga_mensal / 22 / 5)

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
            'horas_trabalhadas': resultado["total_trabalhado"],
            'saldo': resultado["saldo"], 
            'extras': resultado["extras"],
            'deficit': resultado["deficit"]
        })

    return render_template('admin/historico_funcionario.html', funcionario=funcionario.nome, registros=lista, saldo_total=saldo_total, extras_total=extras_total, deficit_total=deficit_total, mes_atual=f"{ano}-{mes:02d}")