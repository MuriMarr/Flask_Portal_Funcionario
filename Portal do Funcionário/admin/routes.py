from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, make_response
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta, timezone
import os, pdfkit

from extensions import db
from models import User, Ponto, Marcacao
from utils import validar_cpf, admin_required, monthrange, to_time, log_action, calcular_banco_horas_acumulado, calcular_trct

admin_bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="templates")

# Funções para administrador
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    funcionarios = User.query.filter_by(empresa_id=current_user.empresa_id, tipo="funcionario").all()
    total_funcionarios = len(funcionarios)

    registros = Ponto.query.join(User).filter(User.empresa_id == current_user.empresa_id).all()
    total_registros = len(registros)

    total_horas = timedelta()
    pendentes = []

    for r in registros:
        marcacoes = Marcacao.query.filter_by(ponto_id=r.id).order_by(Marcacao.hora).all()
        if len(marcacoes) >= 2:
            entrada = datetime.combine(r.data, marcacoes[0].hora)
            saida = datetime.combine(r.data, marcacoes[-1].hora)
            total_horas += (saida - entrada)        
        elif len(marcacoes) == 1:
            pendentes.append(r) 
            
    return render_template('admin_dashboard.html', total_funcionarios=total_funcionarios, total_registros=total_registros, total_horas=total_horas, pendentes=pendentes)

@admin_bp.route("/funcionarios/novo", methods=['GET', 'POST'])
@login_required
@admin_required
def novo_funcionario():
    if request.method == 'POST':
        dados = request.form
        cpf = dados["cpf"].replace(".", "").replace("-", "")
        
        if not validar_cpf(cpf):
            flash("CPF inválido. Digite exatamente 11 números.", "danger")
            return redirect(url_for("admin.novo_funcionario"))

        funcionario = User(
            nome = dados['nome'],
            email = dados['email'],
            cpf = dados['cpf'],
            senha = generate_password_hash(dados['senha'], method='pbkdf2:sha256'),
            telefone = dados['telefone'] or None,
            cargo = dados.get('cargo'),
            salario_mensal = dados.get('salario_mensal', type=float),
            data_nascimento = dados.get('data_nascimento'),
            data_admissao = datetime.now(timezone.utc),
            tipo = "funcionario",
            rua = dados['rua'],
            numero = dados['numero'],
            bairro = dados['bairro'],
            complemento = dados['complemento'],
            cidade_uf = dados['cidade_uf'],
            empresa_id = current_user.empresa_id,
            ativo = True
        )
        db.session.add(funcionario)
        db.session.commit()
        flash('Funcionário cadastrado com sucesso!', 'success')
        return redirect(url_for('admin.funcionarios'))
    
    return render_template('novo_funcionario.html')

@admin_bp.route('/funcionario/<int:id>/desligar', methods=['GET', 'POST'])
@login_required
@admin_required
def desligar_funcionario(id):
    funcionario = User.query.get_or_404(id)
    if funcionario.empresa_id != current_user.empresa_id:
        abort(403)

    if request.method == 'POST':
        funcionario.ativo = False
        funcionario.data_demissao = datetime.now(timezone.utc)
        db.session.commit()
        flash(f'Funcionário {funcionario.nome} desligado.', 'warning')
        return redirect(url_for('admin.funcionarios'))
    
    return render_template('desligar_funcionario.html', funcionario=funcionario)

@admin_bp.route('/funcionarios')
@login_required
@admin_required
def funcionarios():
    funcionarios = User.query.filter_by(empresa_id=current_user.empresa_id, tipo="funcionario").all()
    return render_template('admin_funcionario.html', funcionarios=funcionarios)

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

    return render_template('editar_funcionario.html', funcionario=funcionario)

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

@admin_bp.route("/banco_horas_acumulado/<int:id>")
@login_required
@admin_required
def banco_horas_acumulado(id):
    usuario = User.query.get_or_404(id)

    resultado = calcular_banco_horas_acumulado(usuario)

    return render_template("funcionarios/banco_horas_acumulado.html", funcionario=usuario, resultado=resultado)
 
@admin_bp.route('/trct_pdf/<int:id>')
@login_required
def gerar_trct(id):
    funcionario = User.query.get_or_404(id)
    trct = calcular_trct(funcionario, funcionario.data_demissao)

    rendered_html = render_template("trct_pdf.html", funcionario=funcionario, trct=trct)
    
    WKHTMLTOPDF_PATH = os.environ.get('WKHTMLTOPDF_PATH')
    config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH) if WKHTMLTOPDF_PATH else None
    pdf = pdfkit.from_string(rendered_html, False, configuration=config) if config else pdfkit.from_string(rendered_html, False)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=TRCT_{funcionario.nome}.pdf'
    return response

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

@admin_bp.route('/funcionario/<int:id>/historico')
@login_required
@admin_required
def historico_funcionario(id):
    funcionario = User.query.get_or_404(id)
    ano, mes = datetime.now().year, datetime.now().month
    inicio = datetime(ano, mes, 1).date()
    fim = datetime(ano, mes, monthrange(ano, mes)[1]).date()
    
    registros = Ponto.query.filter(Ponto.user_id == id, Ponto.data >= inicio, Ponto.data <= fim).order_by(Ponto.data.desc()).all()

    jornada_padrao = timedelta(hours=funcionario.empresa.carga_mensal / 22 / 5)
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
            trabalhadas = None

        lista.append({
            'data': r.data,
            'entrada': marcacoes[0].hora.strftime("%H:%M") if marcacoes else '—',
            'saida': marcacoes[-1].hora.strftime("%H:%M") if len(marcacoes) > 1 else '—',
            'horas_trabalhadas': str(trabalhadas) if trabalhadas else '—',
            'saldo': str(saldo) if saldo else '—'
        })

    return render_template('historico_funcionario.html', registros=lista, saldo_total=str(saldo_total), mes_atual=f"{ano}-{mes:02d}")

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

    rendered_html = render_template("holerite.html", funcionario=funcionario, mes=f"{ano}-{mes:02d}", dias=dias_trabalhados, horas=round(total_horas, 2), salario_base=funcionario.salario_mensal, valor_base=valor_base, valor_extras=valor_extras, bruto=bruto, desconto_inss=desconto_inss, desconto_vt=desconto_vt, valor_liquido=liquido)
    
    config = pdfkit.configuration(wkhtmltopdf=r'C:/Arquivos de Programas/wkhtmltopdf/bin/wkhtmltopdf.exe')
    pdf = pdfkit.from_string(rendered_html, False, configuration=config)
   
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=holerite_{funcionario.nome}.pdf'
    return response