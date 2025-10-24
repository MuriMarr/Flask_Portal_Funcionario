import click
from app import create_app, db
from datetime import date, time, datetime, timedelta
from flask.cli import with_appcontext
from models import User, Empresa, Ponto

@click.command("seed")
@with_appcontext
def seed():
    click.echo("Iniciando o seeding do banco de dados...")

    Ponto.query.delete()
    User.query.delete()
    Empresa.query.delete()
    db.session.commit()

    # Empresa fictícia (apenas para referência)
    empresa = Empresa(
        nome="Fujiwara Tofu Co.",
        cnpj="12.345.678/0001-90",
        carga_mensal=220,
        inscricao_estadual="123456789",
        endereco="Rua da Montanha 86",
        email="contato@tofu.jp",
    )
    db.session.add(empresa)
    db.session.commit()

    # Usuário administrador
    admin = User(
        nome="Takumi Fujiwara",
        email="takumi86@tofu.jp",
        cpf="123.456.789-00",
        cargo="Administrador",
        tipo="admin",
        salario_mensal=5000.00,
        data_admissao=date(2020, 1, 15),
        empresa_id=empresa.id,
    )
    admin.set_senha("123456")
    db.session.add(admin)

    # Funcionários
    func1 = User(
        nome="Wataru Akiyama",
        email="wataru86@tofu.jp",
        cpf="987.654.321-00",
        cargo="Motorista",
        tipo="funcionario",
        salario_mensal=3000.00,
        data_admissao=date(2021, 5, 20),
        empresa_id=empresa.id,
    )
    func1.set_senha("turbo86")

    func2 = User(
        nome="Itsuki Takeuchi",
        email="itsuki@tofu.jp",
        cpf="456.789.123-00",
        cargo="Mecânico",
        tipo="funcionario",
        salario_mensal=2800.00,
        data_admissao=date(2022, 3, 10),
        empresa_id=empresa.id,
    )
    func2.set_senha("trueno")

    db.session.add_all([func1, func2])
    db.session.commit()

    # Registros de ponto para os funcionários
    hoje = date.today()
    for i in range(5):
        entrada = datetime.combine(hoje - timedelta(days=i), time(8, 0))
        saida = datetime.combine(hoje - timedelta(days=i), time(17, 0))
        ponto = Ponto(
            data=entrada.date(),
            hora_entrada=entrada.time(),
            hora_saida=saida.time(),
            user_id=func1.id
        )
        db.session.add(ponto)

    db.session.commit()
    
    click.echo("Seeding concluído!")