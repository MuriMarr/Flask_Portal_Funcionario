from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import User, Empresa
from extensions import db
from utils import superadmin_required
from . import superadmin_bp

@superadmin_bp.route("/admins")
@login_required
@superadmin_required
def listar_admins():
    admins = User.query.filter_by(tipo="admin").all()
    return render_template("superadmin/listar_admins.html", admins=admins)

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
    return render_template("superadmin/novo_admin.html", empresas=empresas)

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
    return render_template("superadmin/editar_admin.html", admin=admin, empresas=empresas)

@superadmin_bp.route("/admins/<int:id>/excluir", methods=["POST"])
@login_required
@superadmin_required
def excluir_admin(id):
    admin = User.query.get_or_404(id)
    db.session.delete(admin)
    db.session.commit()
    flash("Administrador excluído com sucesso!", "success")
    return redirect(url_for("superadmin/listar_admins"))