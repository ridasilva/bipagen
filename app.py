import os
import sys
from dotenv import load_dotenv
from flask import Flask
from app.models import db, Usuario, ROLE_ADMIN, Colecao, STATUS_PUBLIC

load_dotenv()

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), "app", "templates"))
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bipagen-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "SQLALCHEMY_DATABASE_URI", "sqlite:///bipagen.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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
    app.run(debug=True, host="0.0.0.0", port=5002)
