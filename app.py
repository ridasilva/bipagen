import os
import sys
from dotenv import load_dotenv
from flask import Flask, request, session
from flask_babel import Babel
from app.models import (
    db,
    Usuario,
    ROLE_ADMIN,
    Colecao,
    STATUS_PUBLIC,
    backfill_codigo_unico,
)

load_dotenv()

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), "app", "templates"))
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bipagen-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "SQLALCHEMY_DATABASE_URI", "sqlite:///bipagen.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["BABEL_DEFAULT_LOCALE"] = "en"
app.config["BABEL_SUPPORTED_LOCALES"] = ["pt", "en", "es"]

babel = Babel()


def get_locale():
    lang = session.get("lang")
    if lang in app.config["BABEL_SUPPORTED_LOCALES"]:
        return lang
    return request.accept_languages.best_match(app.config["BABEL_SUPPORTED_LOCALES"])


babel.init_app(app, locale_selector=get_locale)

db.init_app(app)

from app.routes import main
app.register_blueprint(main)


def migrate_schema():
    inspector = db.inspect(db.engine)
    table = "colecao_microrganismos_qr"
    if table in inspector.get_table_names():
        columns = {col["name"] for col in inspector.get_columns(table)}
        if "status" not in columns:
            db.session.execute(
                db.text(
                    f"ALTER TABLE {table} ADD COLUMN status VARCHAR(20) "
                    f"NOT NULL DEFAULT '{STATUS_PUBLIC}'"
                )
            )
        if "owner_id" not in columns:
            db.session.execute(
                db.text(
                    f"ALTER TABLE {table} ADD COLUMN owner_id INTEGER "
                    "REFERENCES usuarios(id)"
                )
            )
        columns = {col["name"] for col in inspector.get_columns(table)}
        if "codigo_acesso" in columns:
            db.session.execute(
                db.text(f"ALTER TABLE {table} RENAME COLUMN codigo_acesso TO nome_cepa")
            )
        columns = {col["name"] for col in inspector.get_columns(table)}
        if "origem_isolamento" in columns:
            db.session.execute(
                db.text(f"ALTER TABLE {table} RENAME COLUMN origem_isolamento TO origem")
            )
        columns = {col["name"] for col in inspector.get_columns(table)}
        if "temperatura_cultivo" not in columns:
            db.session.execute(
                db.text(
                    f"ALTER TABLE {table} ADD COLUMN temperatura_cultivo VARCHAR(100)"
                )
            )
        columns = {col["name"] for col in inspector.get_columns(table)}
        if "publicacoes" not in columns:
            db.session.execute(
                db.text(f"ALTER TABLE {table} ADD COLUMN publicacoes TEXT")
            )
        columns = {col["name"] for col in inspector.get_columns(table)}
        if "codigo_unico" not in columns:
            db.session.execute(
                db.text(f"ALTER TABLE {table} ADD COLUMN codigo_unico VARCHAR(20)")
            )
        db.session.commit()
        backfill_codigo_unico()
        inspector = db.inspect(db.engine)
        tem_indice_unico = any(
            "codigo_unico" in (ix.get("column_names") or []) and ix.get("unique")
            for ix in inspector.get_indexes(table)
        ) or any(
            "codigo_unico" in (uc.get("column_names") or [])
            for uc in inspector.get_unique_constraints(table)
        )
        if not tem_indice_unico:
            db.session.execute(
                db.text(
                    f"CREATE UNIQUE INDEX uq_colecao_codigo_unico ON {table} "
                    "(codigo_unico)"
                )
            )
            db.session.commit()


def create_admin():
    username = os.environ.get("ADMIN_USERNAME", "admin")
    password = os.environ.get("ADMIN_PASSWORD", "admin123")
    email = os.environ.get("ADMIN_EMAIL", "admin@bipagen.local")
    admin = Usuario.query.filter_by(role=ROLE_ADMIN).first()
    if not admin:
        admin = Usuario.query.filter_by(username=username).first()
    if not admin:
        admin = Usuario(username=username, email=email, role=ROLE_ADMIN)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()


with app.app_context():
    db.create_all()
    migrate_schema()
    create_admin()
    from app.qr_utils import ensure_qr_dir
    ensure_qr_dir()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
