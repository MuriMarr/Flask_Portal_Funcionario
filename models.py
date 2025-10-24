from extensions import db
from flask_login import UserMixin
from datetime import datetime, date, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash

def calcular_horas_ponto(ponto, carga=timedelta(hours=8), limite_extras=2):
    marcacoes = sorted(
        ponto.marcacoes,
        key=lambda m: m.hora)
    total_trabalhado = timedelta()

    pares = {
        "entrada": "saida_almoco",
        "retorno_almoco": "saida_final",
        "extra_inicio": "extra_fim"
    }

    tipos = {m.tipo: m.hora for m in marcacoes}

    for inicio, fim in pares.items():
        if inicio in tipos and fim in tipos:
            h1 = datetime.combine(ponto.data, tipos[inicio])
            h2 = datetime.combine(ponto.data, tipos[fim])
            total_trabalhado += (h2 - h1)

    saldo = total_trabalhado - carga
    limite = timedelta(hours=limite_extras)
    extras = saldo if saldo > timedelta() else timedelta()
    if extras > limite:
        extras = limite
    
    deficit = abs(saldo) if saldo < timedelta() else timedelta()

    return {
        "total_trabalhado": total_trabalhado,
        "carga": carga,
        "saldo": saldo,
        "extras": extras,
        "deficit": deficit,
        "limite_extras": limite
    }

# Modelo de Empresa
class Empresa(db.Model):
    __tablename__ = "empresa"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    carga_mensal = db.Column(db.Integer, default=220)
    inscricao_estadual = db.Column(db.String(50))
    endereco = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120))
    data_cadastro = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    admin_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", name="fk_empresa_admin", use_alter=True), nullable=True)
    
    admin = db.relationship("User", foreign_keys=[admin_id], backref="empresa_administradas")
    users = db.relationship("User", backref="empresa", lazy=True, foreign_keys=lambda: [User.empresa_id])

# Modelo de usuário
class User(UserMixin, db.Model):
    # Dados do usuário
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)  # CPF do funcionário
    telefone = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date)
    cargo = db.Column(db.String(100), nullable=True)
    tipo = db.Column(db.String(20), nullable=False, default="funcionario")  # funcionario ou admin
    
    # Endereço
    rua = db.Column(db.String(150), nullable=True)
    numero = db.Column(db.String(10), nullable=True)
    complemento = db.Column(db.String(50), nullable=True)
    bairro = db.Column(db.String(100), nullable=True)
    cidade = db.Column(db.String(100))
    uf = db.Column(db.String(2))
    
    # Dados do funcionário
    salario_mensal = db.Column(db.Float, nullable=False)  # Salário mensal padrão
    data_admissao = db.Column(db.Date, default=date.today) # Data de admissão
    data_demissao = db.Column(db.Date, nullable=True)  # Data de demissão, se aplicável
    ativo = db.Column(db.Boolean, default=True)
    
    empresa_id = db.Column(db.Integer, db.ForeignKey("empresa.id", name="fk_usuario_empresa"), nullable=True)  # Chave estrangeira para a empresa
    
    pontos = db.relationship("Ponto", backref="user", cascade="all, delete-orphan", passive_deletes=True)
    logs = db.relationship("Log", backref="user", lazy=True)

    def set_senha(self, senha):
        self.senha = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha, senha)
    
# Modelo de Logs
class Log(db.Model):
    __tablename__ = "logs"

    id = db.Column(db.Integer, primary_key=True)
    acao = db.Column(db.String(255), nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)

# Modelo de Aviso
class Aviso(db.Model):
    __tablename__ = "aviso"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    imagem = db.Column(db.String(150))
    criado_em = db.Column(db.DateTime, default=datetime.now(timezone.utc))

# Modelo de Férias
class Ferias(db.Model):
    __tablename__ = "ferias"

    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    inicio = db.Column(db.Date, nullable=False)
    fim = db.Column(db.Date, nullable=False)
    dias = db.Column(db.Integer, nullable=False)
    adiantamento_decimo = db.Column(db.Boolean, default=False)
    aprovado = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default="pendente")  # pendente, aprovado, rejeitado
    
    funcionario = db.relationship("User", backref="ferias")

# Modelo de Ponto
class Ponto(db.Model):
    __tablename__= "pontos"

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)

    marcacoes = db.relationship("Marcacao", backref="ponto", lazy=True, cascade="all, delete-orphan", passive_deletes=True)

class Marcacao(db.Model):
    __tablename__= "marcacoes"

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    tipo = db.Column(db.String(30))
    
    ponto_id = db.Column(db.Integer, db.ForeignKey("pontos.id", ondelete="CASCADE"), nullable=False)