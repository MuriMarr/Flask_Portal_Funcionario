from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import Empresa, User
from extensions import db
from utils import superadmin_required, validar_cnpj
from datetime import datetime, timezone
from . import superadmin_bp

@superadmin_bp.route("/empresas/novo", methods=["GET", "POST"])
@login_required
@superadmin_required
def nova_empresa():
    if request.method == "POST":
        dados = request.form
        nome = dados.get("nome")
        cnpj = ''.join(filter(str.isdigit, dados.get("cnpj", "")))
        endereco = dados.get("endereco")
        email = dados.get("email")
        carga_mensal = dados.get("carga_mensal", type=int) or 220

        if not nome or not cnpj or not endereco:
            flash("Nome, CNPJ e endereço são obrigatórios.", "danger")
            return redirect(url_for("superadmin.nova_empresa"))
        
        if not validar_cnpj(cnpj):
            flash("CNPJ inválido. Digite exatamente 14 números.", "danger")
            return redirect(url_for("superadmin.nova_empresa"))

        empresa = Empresa(
            nome=nome,
            cnpj=cnpj,
            endereco=endereco,
            email=email,
            carga_mensal=carga_mensal,
            data_cadastro=datetime.now(timezone.utc)
        )
        db.session.add(empresa)
        db.session.commit()
        flash("Empresa criada com sucesso!", "success")
        return redirect(url_for("superadmin.dashboard"))

    return render_template("superadmin/nova_empresa.html")

# EDITAR EMPRESA
@superadmin_bp.route("/empresas/<int:id>/editar", methods=["GET", "POST"])
@login_required
@superadmin_required
def editar_empresa(id):
    empresa = Empresa.query.get_or_404(id)

    if request.method == "POST":
        empresa.nome = request.form.get("nome")
        empresa.cnpj = request.form.get("cnpj")
        empresa.endereco = request.form.get("endereco")
        empresa.email = request.form.get("email")
        empresa.carga_mensal = request.form.get("carga_mensal", type=int) or empresa.carga_mensal

        db.session.commit()
        flash("Empresa atualizada com sucesso!", "success")
        return redirect(url_for("superadmin.dashboard"))

    return render_template("superadmin/editar_empresa.html", empresa=empresa)

# EXCLUIR EMPRESA
@superadmin_bp.route("/empresas/<int:id>/excluir", methods=["POST"])
@login_required
@superadmin_required
def excluir_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    db.session.delete(empresa)
    db.session.commit()
    flash("Empresa excluída com sucesso!", "success")
    return redirect(url_for("superadmin.dashboard"))

@superadmin_bp.route("/empresas/<int:id>/definir_admin", methods=["GET", "POST"])
@login_required
@superadmin_required
def definir_admin(id):
    empresa = Empresa.query.get_or_404(id)

    if request.method == "POST":
        admin_id = request.form.get("admin_id", type=int)
        if admin_id:
            admin = User.query.get(admin_id)
            if admin and admin.empresa_id == empresa.id:
                empresa.admin_id = admin.id
                admin.tipo = "admin"
                db.session.commit()
                flash(f"{admin.nome} agora é o admin da empresa {empresa.nome}", "success")
                return redirect(url_for("superadmin.dashboard"))
            else:
                flash("Admin inválido ou não pertence a esta empresa.", "danger")
    
    funcionarios = User.query.filter_by(empresa_id=empresa.id).all()
    return render_template("superadmin/definir_admin.html", empresa=empresa, funcionarios=funcionarios)

@superadmin_bp.route("/empresas")
@login_required
@superadmin_required
def listar_empresas():
    empresas = Empresa.query.all()
    return render_template("superadmin/listar_empresas.html", empresas=empresas)