import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from flask import Flask
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

load_dotenv()

SQLITE_PATH = os.path.join(os.path.dirname(__file__), "instance", "bipagen.db")
MYSQL_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")

if not MYSQL_URI:
    print("ERROR: SQLALCHEMY_DATABASE_URI not set. Run this after docker-compose up.")
    sys.exit(1)

print(f"Source: {SQLITE_PATH}")
print(f"Target: {MYSQL_URI}")

sqlite_engine = create_engine(f"sqlite:///{SQLITE_PATH}")
mysql_engine = create_engine(MYSQL_URI)

from app.models import db, Usuario, Colecao

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = MYSQL_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    print("Creating MySQL tables...")
    db.create_all()

    with Session(sqlite_engine) as src, Session(mysql_engine) as dst:
        # Migrate usuarios
        users = src.query(Usuario).all()
        print(f"Migrating {len(users)} users...")
        for u in users:
            existing = dst.query(Usuario).filter_by(username=u.username).first()
            if existing:
                print(f"  Skipping existing user: {u.username}")
                continue
            new_user = Usuario(
                id=u.id,
                username=u.username,
                email=u.email,
                password_hash=u.password_hash,
                role=u.role,
                data_criacao=u.data_criacao,
            )
            dst.add(new_user)
            print(f"  User: {u.username} ({u.role})")
        dst.commit()

        # Migrate colecao
        strains = src.query(Colecao).all()
        print(f"Migrating {len(strains)} strains...")
        for s in strains:
            existing = dst.query(Colecao).filter_by(nome_cepa=s.nome_cepa).first()
            if existing:
                print(f"  Skipping existing strain: {s.nome_cepa}")
                continue
            new_strain = Colecao(
                id=s.id,
                nome_cepa=s.nome_cepa,
                tipo=s.tipo,
                genero=s.genero,
                especie=s.especie,
                cepa_strain=s.cepa_strain,
                origem=s.origem,
                local_coleta=s.local_coleta,
                data_isolamento=s.data_isolamento,
                meio_cultivo=s.meio_cultivo,
                temperatura_cultivo=s.temperatura_cultivo,
                metodo_preservacao=s.metodo_preservacao,
                local_armazenamento=s.local_armazenamento,
                responsavel=s.responsavel,
                data_cadastro=s.data_cadastro,
                observacoes=s.observacoes,
                publicacoes=s.publicacoes,
                status=s.status,
                owner_id=s.owner_id,
            )
            dst.add(new_strain)
            print(f"  Strain: {s.nome_cepa} ({s.tipo})")
        dst.commit()

    print("Migration complete!")
