from datetime import datetime
from flask import render_template, request, make_response, url_for, redirect, flash
from flask_login import login_required
from extensions import db
from models import User, Ferias
from utils import calcular_pagamento_ferias, admin_required
import pdfkit
from . import admin_bp

# Módulo férias
@admin_bp.route("/ferias/<int:usuario_id>")
@login_required
@admin_required
def ferias_funcionario(usuario_id):
    funcionario = User.query.get_or_404(usuario_id)

    ferias_list = Ferias.query.filter_by(usuario_id=usuario_id).order_by(Ferias.inicio.desc()).all()

    dias_trabalhados = (datetime.now().date() - funcionario.date_admissao).days
    saldo = max(0, (dias_trabalhados // 365) * 30 - sum(f.dias for f in ferias_list))

    return render_template("admin/ferias_admin.html", funcionario=funcionario, ferias_list=ferias_list, saldo=saldo)

@admin_bp.route("ferias/<int:usuario_id>/editar/<int:ferias_id>", methods=["GET", "POST"])
@login_required
@admin_required
def editar_ferias(usuario_id, ferias_id):
    funcionario = User.query.get_or_404(usuario_id)
    ferias = Ferias.query.get_or_404(ferias_id)

    if request.method == "POST":
        ferias.inicio = request.form.get("inicio")
        ferias.fim = request.form.get("fim")
        ferias.dias = request.form.get("dias")
        ferias.adiantamento_decimo = bool(request.form.get("adiantamento_decimo"))
        ferias.aprovado = bool(request.form.get("aprovado"))

        db.session.commit()
        flash("Registro de férias atualizado com sucesso!", "success")
        return redirect(url_for("admin.ferias_funcionario", usuario_id=usuario_id))
    
    return render_template("admin/editar_ferias.html", funcionario=funcionario, ferias=ferias)

@admin_bp.route("/ferias/<int:usuario_id>/excluir/<int:ferias_id>", methods=["POST"])
@login_required
@admin_required
def excluir_ferias(usuario_id, ferias_id):
    ferias = Ferias.query.get_or_404(ferias_id)
    db.session.delete(ferias)
    db.session.commit()
    flash("Registro de férias excluído com sucesso!", "danger")
    return redirect(url_for("admin.ferias_funcionario", usuario_id=usuario_id))

@admin_bp.route("/solicitacoes_ferias")
@login_required
def listar_solicitacoes_ferias():
    solicitacoes = Ferias.query.order_by(Ferias.inicio.asc()).all()
    return render_template("admin/solicitacoes_ferias.html", solicitacoes=solicitacoes)

@admin_bp.route("/ferias/rejeitar/<int:usuario_id>/<int:ferias_id>")
@login_required
@admin_required
def rejeitar_ferias(usuario_id, ferias_id):
    ferias = Ferias.query.get_or_404(ferias_id)
    
    if ferias.status == "REJEITADO":
        db.session.commit()
        flash("Essa solicitação foi rejeitada.", "info")
        return redirect(url_for("admin.ferias_funcionario", usuario_id=usuario_id))
    
    ferias.aprovado = False
    ferias.status = "REJEITADO"
    db.session.commit()

    flash("Solicitação de férias rejeitada.", "warning")
    return redirect(url_for("admin.ferias_funcionario", usuario_id=usuario_id))

@admin_bp.route("/ferias/aprovar/<int:usuario_id>/<int:ferias_id>")
@login_required
@admin_required
def aprovar_ferias(usuario_id, ferias_id):
    ferias = Ferias.query.get_or_404(ferias_id)
    funcionario = User.query.get_or_404(usuario_id)

    if ferias.aprovado:
        flash("Férias já aprovadas.", "info")
        return redirect("admin.ferias_funcionario", usuario_id=usuario_id)
    
    ferias.aprovado = True
    ferias.status = "APROVADO"
    db.session.commit()

    dias_ferias = (ferias.data_fim - ferias.data_inicio).days + 1
    ferias_calc = calcular_pagamento_ferias(funcionario, dias_ferias, ferias.adiantamento_decimo)

    rendered = render_template(
        "ferias_pdf.html",
        funcionario=funcionario,
        ferias=ferias,
        ferias_calc=ferias_calc,
        dias_ferias=dias_ferias,
        total_descontos=round(
            ferias_calc["desconto_inss"]
            + ferias_calc["desconto_irrf"]
            + ferias_calc["desconto_vt"],
            2,
        ),
    )

    config = pdfkit.configuration(
        wkhtmltopdf=r"C:/Arquivos de Programas/wkhtmltopdf/bin/wkhtmltopdf.exe"
    )
    pdf = pdfkit.from_string(rendered, False, configuration=config)

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers[
        "Content-Disposition"
    ] = f'inline; filename="ferias_{funcionario.nome}_{ferias.data_inicio.strftime("%Y-%m-%d")}.pdf"'

    flash("Férias aprovadas e recibo gerado com sucesso!!", "success")
    return response

@admin_bp.route('/ferias/<int:usuario_id>/nova', methods=["GET", "POST"])
@login_required
@admin_required
def nova_ferias(usuario_id):
    funcionario = User.query.get_or_404(usuario_id)

    if request.method == "POST":
        inicio = request.form.get("inicio")
        fim = request.form.get("fim")
        dias = int(request.form.get("dias"))
        adiantamento_decimo = bool(request.form.get("adiantamento_decimo"))

        ferias_calc = calcular_pagamento_ferias(funcionario.salario_mensal, dias, adiantamento_decimo)
        nova_ferias = Ferias(
            funcionario_id=funcionario.id,
            inicio=inicio,
            fim=fim,
            dias=dias,
            adiantamento_decimo=adiantamento_decimo,
            bruto=ferias_calc["bruto"],
            desconto_inss=ferias_calc["desconto_inss"],
            desconto_irrf=ferias_calc["desconto_irrf"],
            valor_liquido=ferias_calc["liquido"],
            aprovado=True
        )
        
        db.session.add(nova_ferias)
        db.session.commit()
        flash("Férias agendadas com sucesso!", "success")
        return redirect(url_for("admin.ferias_funcionario", funcionario_id_id=funcionario.id))
    
    return render_template("admin/nova_ferias.html", funcionario=funcionario)