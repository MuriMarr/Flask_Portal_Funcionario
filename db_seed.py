import click
from flask.cli import with_appcontext
from datetime import datetime, timedelta, timezone
from extensions import db
from models import User, Empresa, Ponto

@click.command("run_seed")
@with_appcontext
def run_seed():
        email_super = "admin@gmail.com"
        superadmin = User.query.filter_by(email=email_super).first()

        if not superadmin:
            superadmin = User (
                nome="Super Administrador",
                email=email_super,
                cpf="12345678910",
                cargo="Superadmin",
                tipo="superadmin",
                ativo=True,
                data_admissao=datetime.now(timezone.utc),
                salario_mensal="999999"
            )
            superadmin.set_senha("admin123")
            db.session.add(superadmin)
            db.session.commit()
            print(f"Superadmin criado: {superadmin.email}")
        else:
            print("Superadmin já existe.")

        # EMPRESA(S)

        empresa = Empresa.query.filter_by(cnpj="12.345.678/0001-99").first()

        if not empresa:
            empresa = Empresa(
                nome="Empresa Exemplo",
                cnpj="12.345.678/0001-99",
                carga_mensal=220,
                endereco="Rua 1, 2 - São Paulo/SP",
                email="contato@exemplo.com",
                data_cadastro=datetime.now(timezone.utc),
                admin_id=superadmin.id,
                inscricao_estadual="0987654321"
            )
            db.session.add(empresa)
            db.session.commit()
            print(f"Empresa criada: {empresa.nome}")
        else:
            print("Empresa já existe.")

        # FUNCIONÁRIOS TESTE

        funcionarios = [
            {
                "nome": "João da Silva",
                "email": "joao@exemplo.com",
                "senha": "123456",
                "cpf": "12345678901",
                "cargo": "Analista",
                "tipo": "funcionario" 
            },
            {
                "nome": "Maria Oliveira",
                "email": "maria@exemplo.com",
                "senha": "1234567",
                "cpf": "98765432100",
                "cargo": "Gerente",
                "tipo": "admin"
            }
        ]

        for f in funcionarios:
            usuario = User.query.filter_by(email=f["email"]).first()
            if not usuario:
                usuario = User(
                    nome=f["nome"],
                    email=f["email"],
                    cpf=f["cpf"],
                    cargo=f["cargo"],
                    tipo=f["tipo"],
                    salario_mensal=f.get("salario_mensal", 3000.0),
                    empresa_id=empresa.id,
                    ativo=True,
                    data_admissao=datetime.now(timezone.utc)
                )
                usuario.set_senha(f["senha"])
                db.session.add(usuario)
                db.session.commit()
                print(f"Usuário criado: {usuario.nome} ({usuario.tipo})")
            else:
                print(f"Usuário já existe: {f['email']}")

            # PONTOS TESTE

            joao = User.query.filter_by(email="joao@exemplo.com").first()
            if joao:
                hoje = datetime.now(timezone.utc)
                ponto_existente = Ponto.query.filter_by(user_id=joao.id, data=hoje).first()
                if not ponto_existente:
                    ponto = Ponto(
                        user_id=joao.id,
                        data=hoje,
                        hora_entrada=datetime.now(timezone.utc),
                        hora_saida=(datetime.now(timezone.utc) + timedelta(hours=8)).time()
                    )
                    db.session.add(ponto)
                    db.session.commit()
                    print(f"Ponto registrado para {joao.nome}")
                else:
                    print(f"Ponto já existe para {joao.nome} hoje.")

if __name__ == "__main__":
    run_seed()