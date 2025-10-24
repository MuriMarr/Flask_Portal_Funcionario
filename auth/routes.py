from datetime import datetime, date, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        user = User.query.filter_by(email=email).first()

        if user and user.check_senha(senha):
            login_user(user, remember=False)
            flash("Login realizado com sucesso", "success")

            if user.tipo == "superadmin": 
                return redirect(url_for("superadmin.dashboard"))
            elif user.tipo == "admin":
                return redirect(url_for("admin.dashboard"))
            elif user.tipo == "funcionario":
                return redirect(url_for("funcionarios.dashboard"))
        else:
            flash("Usuário desconhecido. Contate o suporte.", "danger")

    return render_template("login.html")

@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    if request.method == "POST":
        return ("", 204)
    flash("Logout realizado com sucesso.", "success")
    return redirect(url_for("auth.login"))

@auth_bp.route("/logout_beacon", methods=['POST'])
def logout_beacon():
    try:
        logout_user()
    except Exception:
        pass
    session.clear()
    return ('', 204)

@auth_bp.route('/registrar_funcionario', methods=['GET', 'POST'])
def registrar_ponto():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        data_nascimento = request.form.get('data_nascimento', None)
        cpf = request.form.get('cpf', None)
        cargo = request.form.get('cargo', None)
        try:
            salario_mensal = float(request.form['salario_mensal'] or 0)
        except ValueError:
            salario_mensal = 1940.00
        telefone = request.form.get('telefone', '')
        rua = request.form.get('rua', '')
        numero = request.form.get('numero', '').strip()
        bairro = request.form.get('bairro', '').strip()
        complemento = request.form.get('complemento', '').strip()
        cidade_uf = request.form.get('cidade_uf', '').strip()
        tipo = request.form.get('tipo', 'funcionario')
        data_admissao = request.form.get('data_admissao', '')
        ativo = True

        if not nome or not email or not senha:
            flash('Preencha todos os campos obrigatórios!' 'warning')
            return redirect(url_for('funcionarios.registrar_funcionario'))
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'warning')
            return redirect(url_for('registrar_funcionario'))
        
        novo_user = User(nome=nome, data_nascimento=datetime.strptime(data_nascimento, '%Y-%m-%d'), cpf=cpf, cargo=cargo, salario_mensal=salario_mensal, email=email, senha=generate_password_hash(senha), tipo=tipo, rua=rua, telefone=telefone, cidade_uf=cidade_uf, complemento=complemento, bairro=bairro, numero=numero, data_admissao=datetime.strptime(data_admissao, "%Y-%m-%d").date() if data_admissao else date.today(), ativo=ativo)
        db.session.add(novo_user)
        db.session.commit()
        
        flash('Cadastro realizado com sucesso. Faça login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')