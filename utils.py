import re
from functools import wraps
from flask import abort
from flask_login import current_user
from datetime import datetime, date
from calendar import monthrange
from extensions import db
from models import Log

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

from datetime import date
import calendar

def calcular_trct(funcionario, data_demissao):
    salario_base = funcionario.salario_mensal or 0
    admissao = funcionario.data_admissao
    demissao = data_demissao

    # Se não tem data de admissão ou salário, não calcula nada
    if not admissao or salario_base <= 0:
        return {
            'admissao': admissao.strftime('%d/%m/%Y') if admissao else "—",
            'demissao': demissao.strftime('%d/%m/%Y'),
            'motivo_rescisao': "Sem justa causa",
            'saldo_salario': 0.0,
            'ferias_vencidas': 0.0,
            'ferias_proporcionais': 0.0,
            'decimo_terceiro': 0.0,
            'multa_fgts': 0.0,
            'desconto_inss': 0.0,
            'desconto_vt': 0.0,
            'total_liquido': 0.0
        }

    # Meses trabalhados entre admissão e demissão
    meses_trabalhados = (demissao.year - admissao.year) * 12 + (demissao.month - admissao.month)

    # Dias trabalhados no mês da demissão
    dias_no_mes = calendar.monthrange(demissao.year, demissao.month)[1]
    dias_trabalhados = (demissao - max(admissao, date(demissao.year, demissao.month, 1))).days + 1

    # Se não houve meses nem dias de trabalho, retorna TRCT zerado
    if meses_trabalhados <= 0 and dias_trabalhados <= 0:
        return {
            'admissao': admissao.strftime('%d/%m/%Y'),
            'demissao': demissao.strftime('%d/%m/%Y'),
            'motivo_rescisao': "Sem justa causa",
            'saldo_salario': 0.0,
            'ferias_vencidas': 0.0,
            'ferias_proporcionais': 0.0,
            'decimo_terceiro': 0.0,
            'multa_fgts': 0.0,
            'desconto_inss': 0.0,
            'desconto_vt': 0.0,
            'total_liquido': 0.0
        }

    # 1. Saldo de salário proporcional
    saldo_salario = round((salario_base / dias_no_mes) * max(dias_trabalhados, 0), 2)

    # 2. Férias vencidas + 1/3 (só se já completou 1 ano)
    ferias_vencidas = 0.0
    if (demissao - admissao).days >= 365:
        ferias_vencidas = round(salario_base + (salario_base / 3), 2)

    # 3. Férias proporcionais + 1/3
    ferias_base = (salario_base / 12) * max(meses_trabalhados, 0)
    ferias_proporcionais = round(ferias_base + (ferias_base / 3), 2)

    # 4. 13º salário proporcional
    decimo_terceiro = round((salario_base / 12) * max(demissao.month, 0), 2)

    # 5. Multa do FGTS
    total_fgts = round((salario_base * 0.08) * max(meses_trabalhados, 0), 2)
    multa_fgts = round(total_fgts * 0.4, 2)

    # 6. Descontos
    desconto_inss = round(salario_base * 0.08, 2)
    desconto_vt = round(salario_base * 0.05, 2)

    # 7. Total líquido
    total_liquido = round(saldo_salario + ferias_vencidas + ferias_proporcionais +
                          decimo_terceiro + multa_fgts - desconto_inss - desconto_vt, 2)

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


def validar_cnpj(cnpj: str) -> bool:
    return bool(re.fullmatch(r"\d{14}", cnpj))

def validar_cpf(cpf: str) -> bool:
    return bool(re.fullmatch(r"\d{11}", cpf))

def format_timedelta(td):
    if not td or not hasattr(td, "total_seconds"):
        return "-"
    total_seconds = int(td.total_seconds())
    horas, resto = divmod(total_seconds, 3600)
    minutos, _ = divmod(resto, 60)
    return f"{horas}h{minutos:02d}min"

def calcular_saldo_ferias(funcionario, hoje=None):
    hoje = hoje or date.today()
    admissao = funcionario.data_admissao

    meses = (hoje.year - admissao.year) * 12 + (hoje.month - admissao.month)
    dias_direito = (meses // 12) * 30 + (meses % 12) * 2.5
    dias_gozados = sum(f.ferias_dias for f in funcionario.ferias if f.status == "concedida")

    return round(dias_direito - dias_gozados, 1)

def calcular_pagamento_ferias(funcionario, dias=30, adiantamento_decimo=False):
    salario_base = float(funcionario.salario_mensal or 0)
    dias = min(dias, 30)

    valor_ferias = (salario_base / 30) * dias
    adicional_ferias = valor_ferias / 3
    bruto = valor_ferias + adicional_ferias

    def calcular_inss(valor):
        if valor <= 1518.00:
            return valor * 0.075
        elif valor <= 2793.88:
            return valor * 0.09
        elif valor <= 4190.83:
            return valor * 0.12
        elif valor <= 8157.41:
            return valor * 0.14
        else:
            return 951.58

    desconto_inss = round(calcular_inss(bruto), 2)

    def calcular_irrf(valor):
        base = valor - desconto_inss
        if base <= 2428.80:
            return 0.0
        elif base <= 2826.65:
            return base * 0.075 - 182.16
        elif base <= 3751.05:
            return base * 0.15 - 394.16
        elif base <= 4664.68:
            return base * 0.225 - 675.49
        else:
            return base * 0.275 - 908.73
        
    desconto_irrf = round(max(calcular_irrf(bruto), 0), 2)
    
    desconto_vt = round(bruto * 0.06, 2)

    total_descontos = desconto_inss + desconto_irrf + desconto_vt
    liquido = round(bruto - total_descontos, 2)

    adiantamento_decimo = round(salario_base / 2, 2) if adiantamento_decimo else 0
    return {
        "salario_base": salario_base,
        "dias_ferias": dias,
        "valor_ferias": round(valor_ferias, 2),
        "adicional_ferias": round(adicional_ferias, 2),
        "bruto": round(bruto, 2),
        "desconto_inss": desconto_inss,
        "desconto_irrf": desconto_irrf,
        "desconto_vt": desconto_vt,
        "total_descontos": total_descontos,
        "liquido": liquido,
        "adiantamento_13": adiantamento_decimo
    }