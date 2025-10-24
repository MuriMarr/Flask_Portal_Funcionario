from calendar import monthrange
from datetime import datetime
from flask import Blueprint, render_template, make_response
from models import User, Ponto, Marcacao, Ferias
from flask_login import login_required, current_user
from utils import calcular_trct, admin_required, calcular_pagamento_ferias
from routes import admin_bp, funcionarios_bp
from routes.common.pdf_utils import gerar_pdf

# Modelos de documentos, DP e RH
@admin_bp.route('/trct_pdf/<int:id>')
@login_required
def gerar_trct(id):
    funcionario = User.query.get_or_404(id)
    trct = calcular_trct(funcionario, funcionario.data_demissao)
    
    pdf = gerar_pdf("documentos/trct_pdf.html", funcionario=funcionario, trct=trct)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=TRCT_{funcionario.nome}.pdf'
    return response

@admin_bp.route('/funcionario/<int:id>/holerite')
@login_required
@admin_required
def holerite_funcionario(id):
    funcionario = User.query.get_or_404(id)
    ano, mes = datetime.now().year, datetime.now().month
    inicio = datetime(ano, mes, 1).date()
    fim = datetime(ano, mes, monthrange(ano, mes)[1]).date()

    registros = Ponto.query.filter(Ponto.user_id == id, Ponto.data >= inicio, Ponto.data <= fim).all()

    jornada_dia = funcionario.empresa.carga_mensal / 22
    valor_hora = funcionario.salario_mensal / funcionario.empresa.carga_mensal
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

    # Cálculo do salário
    valor_base = round(total_horas * valor_hora, 2)
    valor_extras = round(extras * valor_hora * 1.5, 2) # Total de horas extras
    bruto = valor_base + valor_extras

    desconto_inss = round(bruto * 0.08, 2)  # 8% de INSS
    desconto_vt = round(bruto * 0.05, 2)  # 5% de vale transporte
    liquido = round(bruto - desconto_inss - desconto_vt, 2) # Salário líquido
   
    pdf = gerar_pdf("documentos/holerite_pdf.html", funcionario=funcionario, mes=f"{ano}-{mes:02d}", dias=dias_trabalhados, horas=round(total_horas, 2), salario_base=funcionario.salario_mensal, valor_base=valor_base, valor_extras=valor_extras, bruto=bruto, desconto_inss=desconto_inss, desconto_vt=desconto_vt, valor_liquido=liquido)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=holerite_{funcionario.nome}.pdf'
    return response

## FUNÇÕES DE PDF PARA ADMIN ##
def gerar_ferias_pdf_admin(usuario_id, ferias_id):
    funcionario = User.query.get_or_404(usuario_id)
    ferias = Ferias.query.get_or_404(ferias_id)

    ferias_calc = calcular_pagamento_ferias(
        funcionario=funcionario,
        ferias=ferias,
        adiantamento_decimo=getattr(ferias, "adiantamento_decimo", False)
    )

    rendered = render_template(
        "documentos/ferias_pdf.html",
        funcionario=funcionario,
        ferias=ferias,
        ferias_calc=ferias_calc
    )

    pdf = gerar_pdf(rendered)
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=ferias_{funcionario.id}_{ferias.id}.pdf"
    return response

@admin_bp.route("/ferias/pdf/<int:id>")
@login_required
def gerar_pdf_ferias(ferias_id):
    ferias = Ferias.query.get_or_404(ferias_id)
    funcionario = ferias.funcionario

    pagamento = calcular_pagamento_ferias(funcionario, ferias)

    rendered = render_template("documentos/ferias_pdf.html", funcionario=funcionario, ferias=ferias, pagamento=pagamento)

    pdf = gerar_pdf(rendered)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=ferias_{ferias.id}.pdf'
    return response

## FUNÇÕES DE PDF PARA FUNCIONÁRIOS ##
def gerar_ferias_pdf(ferias_id):
    ferias = Ferias.query.get_or_404(ferias_id)
    funcionario = current_user.id

    ferias_calc = calcular_pagamento_ferias(
        funcionario=funcionario,
        ferias=ferias,
        adiantamento_decimo=ferias.adiantamento_decimo if hasattr(ferias, "adiantamento_decimo") else False
    )

    rendered = render_template(
        "documentos/ferias_pdf.html",
        funcionario=funcionario,
        ferias=ferias,
        ferias_calc=ferias_calc
    )

    pdf = gerar_pdf(rendered)

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Type"] = f"inline; filename=ferias_{ferias.id}.pdf"
    return response

@funcionarios_bp.route('/holerite')
@login_required
def holerite(user_id=None):
    if current_user.tipo == "admin" and user_id:
        funcionario = User.query.get_or_404(user_id)
        is_admin = True
    else:
        funcionario = current_user
        is_admin = False

    ano, mes = datetime.now().year, datetime.now().month
    inicio = datetime(ano, mes, 1).date()
    fim = datetime(ano, mes, monthrange(ano, mes)[1]).date()

    registros = Ponto.query.filter(Ponto.user_id == current_user.id, Ponto.data >= inicio, Ponto.data <= fim).all()
    
    jornada_dia = current_user.empresa.carga_mensal / 22
    valor_hora = current_user.salario_mensal / current_user.empresa.carga_mensal

    total_horas = extras = dias_trabalhados = 0

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
    
    rendered = render_template("documentos/holerite_pdf.html", funcionario=current_user, mes=f"{ano}={mes:02d}", dias=dias_trabalhados, horas=round(total_horas, 2), salario_base=current_user.salario_mensal, valor_base=valor_base, valor_extras=valor_extras, bruto=bruto, desconto_inss=desconto_inss, desconto_vt=desconto_vt, valor_liquido=liquido)

    pdf = gerar_pdf(rendered)
    
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=holerite_{mes}.pdf'
    return response