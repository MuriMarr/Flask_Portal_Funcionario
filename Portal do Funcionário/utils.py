import re
from functools import wraps
from flask import abort
from flask_login import current_user
from datetime import datetime, date, timedelta
from calendar import monthrange
from extensions import db
from models import Log, Ponto

# Decorators
def superadmin_required(f):
    @wraps(f)
    def funcao_decorada(*args, **kwargs):
        if current_user.tipo != 'superadmin':
            abort(403)
        return f(*args, **kwargs)    
    return funcao_decorada

def admin_required(func):
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo not in ['admin', 'superadmin']:
            abort(403)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

def month_range(ano: int, mes: int):
    primeiro = date(ano, mes, 1)
    ultimo = date(ano, mes, monthrange(ano, mes)[1])
    return primeiro, ultimo

# Ações de log
def log_action(usuario, acao):
    novo_log = Log(usuario_id=usuario.id, acao=acao)
    db.session.add(novo_log)
    db.session.commit()

def to_time(d, h):
    if not h:
        return None
    if isinstance(h, str):
        try:
            h_time = datetime.strptime(h, "%H:%M:%S").time()
        except ValueError:
            return None
    else:
        h_time = h
    return datetime.combine(d if isinstance(d, date) else date.today(), h_time)

def calcular_trct(funcionario, data_demissao):
    salario_base = funcionario.salario_mensal
    admissao = funcionario.data_admissao
    demissao = data_demissao

    # 1. Saldo de salário
    dias_trabalhados = demissao.day
    saldo_salario = round((salario_base / 30) * dias_trabalhados, 2)

    # 2. Férias vencidas + 1/3
    ferias_vencidas = round(salario_base + (salario_base / 3), 2)

    # 3. Férias proporcionais + 1/3
    meses_trabalhados = (demissao.year - admissao.year) * 12 + (demissao.month - admissao.month)
    ferias_proporcionais = round(((salario_base / 12) * meses_trabalhados) + (((salario_base / 12) * meses_trabalhados) / 3), 2)

    # 4. 13º salário proporcional
    decimo_terceiro = round((salario_base / 12) * data_demissao.month, 2)

    # 5. Multa do FGTS
    total_fgts = round((salario_base * 0.08) * meses_trabalhados, 2)  # Considerando 8% de FGTS
    multa_fgts = round(total_fgts * 0.4, 2)  # 40% de multa sobre o FGTS

    # 6. Descontos
    desconto_inss = round(salario_base * 0.08, 2)  # 8% de INSS
    desconto_vt = round(salario_base * 0.05, 2)  # 5% de vale transporte

    # 7. Total do TRCT
    total_liquido = round(saldo_salario + ferias_vencidas + ferias_proporcionais + decimo_terceiro + multa_fgts - desconto_inss - desconto_vt, 2)
    return {
        'admissao': admissao.strftime('%d/%m/%Y'),
        'demissao': demissao.strftime('%d/%m/%Y'),
        'motivo_rescisao': "Sem justa causa",
        'saldo_salario': saldo_salario,
        'ferias_vencidas': ferias_vencidas,
        'ferias_proporcionais': ferias_proporcionais,
        'decimo_terceiro': decimo_terceiro,
        'multa_fgts': multa_fgts,
        'desconto_inss': desconto_inss,
        'desconto_vt': desconto_vt,
        'total_liquido': total_liquido
    }

def calcular_banco_horas_acumulado(usuario, ate_data=None):
    if ate_data is None:
        ate_data = datetime.now()
    
    registros = (Ponto.query
            .filter(Ponto.user_id == usuario.id)
            .filter(Ponto.data <= ate_data.date())
            .order_by(Ponto.data)
            .all()
    )

    total_trabalhadas = timedelta()
    historico_mensal = {}
    saldo_acumulado = timedelta()

    carga_mensal_horas = usuario.empresa.carga_mensal or 220
    carga_mensal = timedelta(hours=carga_mensal_horas)

    for r in registros:
        if r.hora_entrada and r.hora_saida:
            entrada = datetime.combine(r.data, r.hora_entrada)
            saida = datetime.combine(r.data, r.hora_saida)
            trabalhado = saida - entrada
            total_trabalhadas += trabalhado

            mes = r.data.strftime("%Y-%m")
            if mes not in historico_mensal:
                historico_mensal[mes] = {"total_trabalhadas": timedelta(), "saldo": timedelta()}
            
            historico_mensal[mes]["total_trabalhadas"] += trabalhado
    
    for mes, dados in historico_mensal.items():
        saldo_mes = dados["total_trabalhadas"] - carga_mensal
        historico_mensal[mes]["saldo"] = saldo_mes
        saldo_acumulado += saldo_mes

    return {
        "total_trabalhadas": total_trabalhadas,
        "saldo_acumulado": saldo_acumulado,
        "historico_mensal": historico_mensal
    }
def validar_cnpj(cnpj: str) -> bool:
    return bool(re.fullmatch(r"\d{14}", cnpj))

def validar_cpf(cpf: str) -> bool:
    return bool(re.fullmatch(r"\d{11}", cpf))