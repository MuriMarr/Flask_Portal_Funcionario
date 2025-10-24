from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Empresa, User
from utils import superadmin_required, admin_required
from . import empresas_bp

@empresas_bp.route("/")
@login_required
@superadmin_required
def lista_empresas():
    empresas = Empresa.query.all()
    return render_template("lista_empresas.html", empresas=empresas)

@empresas_bp.route("/nova_empresa", methods=["GET", "POST"])
@login_required
@superadmin_required
def nova_empresa():
    if request.method == "POST":
        nome = request.form.get("nome")
        cnpj = request.form.get("cnpj")
        inscricao_estadual = request.form.get("inscricao_estadual")
        endereco = request.form.get("endereco")
        telefone = request.form.get("telefone")
        email = request.form.get("email")
        carga_mensal = int(request.form.get("carga_mensal", 220))

        empresa = Empresa(nome=nome, cnpj=cnpj, carga_mensal=carga_mensal, inscricao_estadual=inscricao_estadual, endereco=endereco, telefone=telefone, email=email)
        db.session.add(empresa)
        db.session.commit()
        flash("Empresa cadastrada com sucesso!", "success")
        return redirect(url_for("empresas.lista_empresas"))
    
    return render_template("cadastro_empresas.html")

@empresas_bp.route("/<int:empresa_id>/funcionarios", methods=["GET", "POST"])
@login_required
@admin_required
def gerenciar_funcionarios(empresa_id):
    empresa = Empresa.query.get_or_404(current_user.empresa_id)

    if request.method == "POST":
        funcionario_id = request.form.get("funcionario_id")
        funcionario = User.query.get(funcionario_id)
        if funcionario:
            funcionario.empresa_id = empresa.id
            db.session.commit()
            flash(f"{funcionario.nome} associado à {empresa.nome}", "success")
        return redirect(url_for("empresas.gerenciar_funcionarios", empresa_id=empresa.id))
    
    funcionarios = User.query.filter_by(tipo="funcionario").all()
    return render_template("empresa_funcionarios.html", empresa=empresa, funcionarios=funcionarios)

@empresas_bp.route("/<int:empresa_id>/remover_funcionario/<int:user_id>")
@login_required
@admin_required
def remover_vinculo(empresa_id, user_id):
    empresa = Empresa.query.get_or_404(current_user.empresa_id)
    funcionario = User.query.get_or_404(user_id)

    if funcionario.empresa_id == empresa.id:
        funcionario.empresa_id = None
        db.session.commit()
        flash(f"Vínculo com {funcionario.nome} encerrado!", "info")
        
    return redirect(url_for("empresas.gerenciar_funcionarios", empresa_id=empresa.id))

@empresas_bp.route("/<int:empresa_id>/editar", methods=["GET", "POST"])
@login_required
def editar_empresa(empresa_id):
    empresa = Empresa.query.get_or_404(empresa_id)
    
    if request.method == "POST":
        empresa.nome = request.form.get("nome")
        empresa.cnpj = request.form.get("cnpj")
        empresa.inscricao_estadual = request.form.get("inscricao_estadual")
        empresa.endereco = request.form.get("endereco")
        empresa.telefone = request.form.get("telefone")
        empresa.email = request.form.get("email")
        empresa.carga_mensal = int(request.form.get("carga_mensal", 220))

        db.session.commit()
        flash("Empresa atualizada com sucesso!", "success")
        return redirect(url_for("empresas.lista_empresas"))
    
    return render_template("editar_empresa.html", empresa=empresa)

@empresas_bp.route("/<int:empresa_id>/deletar")
@login_required
def deletar_empresa(empresa_id):
    empresa = Empresa.query.get_or_404(empresa_id)
    db.session.delete(empresa)
    db.session.commit()
    flash("Empresa deletada com sucesso!", "success")
    return redirect(url_for("empresas.lista_empresas"))