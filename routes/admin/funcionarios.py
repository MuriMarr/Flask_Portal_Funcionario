from datetime import datetime, timezone
from flask import abort, render_template, url_for, redirect, flash, request
from flask_login import current_user, login_required
from extensions import db
from models import User
from utils import validar_cpf, admin_required
from werkzeug.security import generate_password_hash
from . import admin_bp

# Módulo de funcionários
@admin_bp.route('/funcionarios')
@login_required
@admin_required
def funcionarios():
    funcionarios = User.query.filter_by(empresa_id=current_user.empresa_id, tipo="funcionario").all()
    return render_template('admin/admin_funcionario.html', funcionarios=funcionarios)

@admin_bp.route("/funcionarios/novo", methods=['GET', 'POST'])
@login_required
@admin_required
def novo_funcionario():
    if request.method == 'POST':
        dados = request.form
        
        nome = dados.get("nome")
        cpf = dados["cpf"].replace(".", "").replace("-", "")
        cargo = dados.get("cargo")
        email = dados.get("email")
        senha = dados.get("senha")

        if not validar_cpf(cpf):
            flash("CPF inválido. Digite exatamente 11 números.", "danger")
            return redirect(url_for("admin.novo_funcionario"))
        
        if not nome or not cpf or not cargo or not email or not senha:
            flash("Preencha os campos obrigatórios (nome, CPF, cargo, email e senha).", "danger")
            return redirect(url_for("admin.novo_funcionario"))
        
        raw_salario = dados.get("salario_mensal")
        salario = 0.0
        if raw_salario:
            raw_salario = raw_salario.replace("R$", "").replace(".", "").replace(",", ".").strip()
            try:
                salario = float(raw_salario)
            except ValueError:
                flash("valor de salário inválido, Corrija e tente novamente", "danger")
                return redirect(url_for("admin.novo_funcionario"))
            else:
                flash("Salário não informado.", "warning")

        funcionario = User(
            nome = dados['nome'],
            data_nascimento = dados.get('data_nascimento'),
            cpf = dados['cpf'],
            telefone = dados['telefone'] or None,
            rua = dados['rua'],
            numero = dados['numero'],
            complemento = dados['complemento'],
            bairro = dados['bairro'],
            cidade = dados.get('cidade'),
            uf = dados['uf'],
            cargo = dados['cargo'],
            salario_mensal = salario,
            email = dados['email'],
            senha = generate_password_hash(dados['senha'], method='pbkdf2:sha256'),
            data_admissao = datetime.now(timezone.utc),
            tipo = "funcionario",
            empresa_id = current_user.empresa_id,
            ativo = True
        )
        db.session.add(funcionario)
        db.session.commit()
        flash('Funcionário cadastrado com sucesso!', 'success')
        return redirect(url_for('admin.funcionarios'))
    
    return render_template('admin/novo_funcionario.html')

@admin_bp.route('/funcionario/<int:id>/desligar', methods=['GET', 'POST'])
@login_required
@admin_required
def desligar_funcionario(id):
    funcionario = User.query.get_or_404(id)
    if funcionario.empresa_id != current_user.empresa_id:
        abort(403)

    if request.method == 'POST':
        funcionario.ativo = False
        funcionario.data_demissao = datetime.now(timezone.utc).date()
        db.session.commit()
        flash(f'Funcionário {funcionario.nome} desligado.', 'warning')
        return redirect(url_for('admin.funcionarios'))
    
    return render_template('admin/desligar_funcionario.html', funcionario=funcionario)

@admin_bp.route('/funcionario/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_funcionario(id):
    funcionario = User.query.get_or_404(id)
    if funcionario.empresa_id != current_user.empresa_id:
        abort(403)

    if request.method == 'POST':
        funcionario.nome = request.form.get('nome')
        funcionario.email = request.form.get('email')
        funcionario.cargo = request.form.get('cargo')
        funcionario.salario_mensal = float(request.form.get('salario_mensal'))
        db.session.commit()
        flash('Funcionário atualizado com sucesso.', 'success')
        return redirect(url_for('admin.funcionarios'))
        
    outro_user = User.query.filter(User.email == funcionario.email, User.id != funcionario.id).first()
    if outro_user:
        flash('Este email já está sendo usado por outro funcionário.', 'warning')

    return render_template('admin/editar_funcionario.html', funcionario=funcionario)

@admin_bp.route('/funcionario/<int:id>/excluir')
@login_required
@admin_required
def excluir_funcionario(id):
    funcionario = User.query.get_or_404(id)
    if funcionario.empresa_id != current_user.empresa_id:
        abort(403)

    db.session.delete(funcionario)
    db.session.commit()
    flash('Funcionário excluído com sucesso.', 'success')
    return redirect(url_for('admin.funcionarios'))
