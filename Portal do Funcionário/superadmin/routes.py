from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import Empresa, User, Ponto
from utils import superadmin_required, validar_cnpj
from datetime import datetime, timezone

superadmin_bp = Blueprint("superadmin", __name__, url_prefix="/superadmin", template_folder="templates")

# DASHBOARD
@superadmin_bp.route("/dashboard")
@login_required
@superadmin_required
def dashboard():
    total_empresas = Empresa.query.count()
    total_admins = User.query.filter_by(tipo="admin").count()
    total_funcionarios = User.query.filter_by(tipo="funcionario").count()
    total_horas = db.session.query(Ponto).count()
    
    empresas = Empresa.query.all()
    return render_template("super_dashboard.html", total_empresas=total_empresas, total_admins=total_admins, total_funcionarios=total_funcionarios, total_horas=total_horas, empresas=empresas)

# NOVA EMPRESA
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

    return render_template("nova_empresa.html")

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

    return render_template("editar_empresa.html", empresa=empresa)

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
    return render_template("definir_admin.html", empresa=empresa, funcionarios=funcionarios)

@superadmin_bp.route("/empresas")
@login_required
@superadmin_required
def listar_empresas():
    empresas = Empresa.query.all()
    return render_template("listar_empresas.html", empresas=empresas)

#--ADMINS--#
@superadmin_bp.route("/admins")
@login_required
@superadmin_required
def listar_admins():
    admins = User.query.filter_by(tipo="admin").all()
    return render_template("listar_admins.html", admins=admins)

@superadmin_bp.route("/admins/novo", methods=["GET", "POST"])
@login_required
@superadmin_required
def novo_admin():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")
        telefone = request.form.get("telefone")
        empresa_id = request.form.get("empresa_id")

        if not nome or not email or not senha or not empresa_id:
            flash("Preencha os dados obrigatórios.", "danger")
            return redirect(url_for("superadmin.novo_admin"))
        
        if User.query.filter_by(email=email).first():
            flash("Já existe um usuário com este email.", "danger")
            return redirect(url_for("superadmin.novo_admin"))
        
        admin = User(
            nome=nome,
            email=email,
            telefone=telefone,
            tipo="admin",
            empresa_id=empresa_id,
        )
        admin.set_senha(senha)
        db.session.add(admin)
        db.session.commit()

        flash("Administrador criado com sucesso!", "sucess")
        return redirect(url_for("superadmin.listar_admins"))
    
    empresas = Empresa.query.all()
    return render_template("novo_admin.html", empresas=empresas)

@superadmin_bp.route("/admins/<int:id>/editar", methods=["GET", "POST"])
@login_required
@superadmin_required
def editar_admin(id):
    admin = User.query.get_or_404(id)
    if request.method == "POST":
        admin.nome = request.form.get("nome")
        admin.email = request.form.get("email")
        admin.telefone = request.form.get("telefone")
        admin.empresa_id = request.form.get("empresa_id")
        db.session.commit()
        flash("Administrador atualizado com sucesso.", "success")
        return redirect(url_for("superadmin.listar_admins"))

    empresas = Empresa.query.all()
    return render_template("editar_admin.html", admin=admin, empresas=empresas)

@superadmin_bp.route("/admins/<int:id>/excluir", methods=["POST"])
@login_required
@superadmin_required
def excluir_admin(id):
    admin = User.query.get_or_404(id)
    db.session.delete(admin)
    db.session.commit()
    flash("Administrador excluído com sucesso!", "success")
    return redirect(url_for("superadmin.listar_admins"))