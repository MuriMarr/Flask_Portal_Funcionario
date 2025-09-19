from flask import Blueprint, render_template, redirect, url_for, flash, make_response
from flask_login import login_required, current_user
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import pdfkit

from extensions import db
from models import Ponto, Aviso, Marcacao, calcular_horas_ponto
from utils import monthrange

funcionarios_bp = Blueprint('funcionarios', __name__, url_prefix='/funcionarios', template_folder='templates')

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

    return render_template("funcionario_dashboard.jinja2", horas_trabalhadas=round(total_trabalhado, 2), horas_extras=round(total_extras, 2), banco_horas=round(banco_horas, 2), proximo_pagamento=proximo_pagamento, semanas=semanas, horas_semanais=horas_semanais_list, extras_semanais=extras_semanais_list)

@funcionarios_bp.route('/registrar_ponto', methods=["GET", "POST"])
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

    return redirect(url_for("funcionarios.dashboard"))
    
@funcionarios_bp.route('/historico')
@login_required
def historico():
    ano, mes = datetime.now().year, datetime.now().month
    inicio = datetime(ano, mes, 1).date()
    fim = datetime(ano, mes, monthrange(ano, mes)[1]).date()

    registros = Ponto.query.filter(Ponto.user_id == current_user.id, Ponto.data >= inicio, Ponto.data <= fim).order_by(Ponto.data.desc()).all()
    
    jornada_padrao = timedelta(hours=current_user.empresa.carga_mensal / 22 / 5)
    saldo_total = timedelta()
    lista = []

    for r in registros:
        marcacoes = Marcacao.query.filter_by(ponto_id=r.id).order_by(Marcacao.hora).all()
        if len(marcacoes) >= 2:
            entrada = datetime.combine(r.data, marcacoes[0].hora)
            saida = datetime.combine(r.data, marcacoes[-1].hora)
            trabalhadas = saida - entrada
            saldo = trabalhadas - jornada_padrao
            saldo_total += saldo
        else:
            trabalhadas = saldo = None

        lista.append({
            'data': r.data,
            'entrada': marcacoes[0].hora.strftime("%H:%M") if marcacoes else '—',
            'saida': marcacoes[-1].hora.strftime("%H:%M") if len(marcacoes) > 1 else '—',
            'horas_trabalhadas': trabalhadas if trabalhadas else '—',
            'saldo': str(saldo) if saldo else '—'
        })

    return render_template('historico.html', registros=lista, saldo_total=saldo_total, mes_atual=f"{ano}-{mes:02d}")

@funcionarios_bp.route('/banco_horas')
@login_required
def banco_horas():
    pontos = Ponto.query.filter_by(usuario_id=current_user.id).all()
    saldo = 0
    for p in pontos:
        if p.hora_entrada and p.hora_saida:
            entrada = datetime.combine(p.data, p.hora_entrada)
            saida = datetime.combine(p.data, p.hora_saida)
            saldo += (saida - entrada).seconds // 3600

    return render_template('banco_horas.html', pontos=pontos)

@funcionarios_bp.route('/holerite')
@login_required
def holerite():
    ano, mes = datetime.now().year, datetime.now().month
    inicio = datetime(ano, mes, 1).date()
    fim = datetime(ano, mes, monthrange(ano, mes)[1]).date()

    registros = Ponto.query.filter(Ponto.user_id == current_user.id, Ponto.data >= inicio, Ponto.data <= fim).all()
    
    jornada_dia = current_user.empresa.carga_mensal / 22
    valor_hora = current_user.salario_mensal / current_user.empresa.carga_mensal

    total_horas = extras = 0
    dias_trabalhados = 0

    for r in registros:
        marcacoes = Marcacao.query.filter_by(ponto_id=r.id).order_by(Marcacao.hora).all()
        if len(marcacoes) >= 2:
            entrada, saida = marcacoes[0].hora, marcacoes[-1].hora
            horas = (datetime.combine(r.data, saida) - datetime.combine(r.data, entrada)).total_seconds() / 3600
            total_horas += horas
            dias_trabalhados += 1
            if horas > jornada_dia:
                extras += (horas - jornada_dia)

    valor_base = round(total_horas * valor_hora, 2)
    valor_extras = round(extras * valor_hora * 1.5, 2)
    bruto = valor_base + valor_extras

    desconto_inss = round(bruto * 0.08, 2)
    desconto_vt = round(bruto * 0.05, 2)
    liquido = round(bruto - desconto_inss - desconto_vt)
    
    rendered_html = render_template("holerite.html", funcionario=current_user, mes=f"{ano}={mes:02d}", dias=dias_trabalhados, horas=round(total_horas, 2), salario_base=current_user.salario_mensal, valor_base=valor_base, valor_extras=valor_extras, bruto=bruto, desconto_inss=desconto_inss, desconto_vt=desconto_vt, valor_liquido=liquido)
    
    config = pdfkit.configuration(wkhtmltopdf=r'C:/Arquivos de Programas/wkhtmltopdf/bin/wkhtmltopdf.exe')
    pdf = pdfkit.from_string(rendered_html, False, configuration=config)
    
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=holerite_{mes}.pdf'
    return response