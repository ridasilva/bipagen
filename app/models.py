import re
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import event, or_, select
from werkzeug.security import generate_password_hash, check_password_hash

from app.qr_utils import qr_safe_name

db = SQLAlchemy()

CODIGO_UNICO_PREFIXO = "GHG"
CODIGO_UNICO_DIGITOS = 5
_codigo_unico_re = re.compile(r"^%s(\d+)$" % CODIGO_UNICO_PREFIXO)

ROLE_ADMIN = "admin"
ROLE_EDITOR = "editor"
ROLE_VIEWER = "viewer"

STATUS_PUBLIC = "public"
STATUS_PRIVATE = "private"


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_VIEWER)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == ROLE_ADMIN

    @property
    def is_editor(self):
        return self.role == ROLE_EDITOR

    def can_edit(self):
        return self.role in (ROLE_ADMIN, ROLE_EDITOR)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "data_criacao": str(self.data_criacao) if self.data_criacao else "",
        }


class Colecao(db.Model):
    __tablename__ = "colecao_microrganismos_qr"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_unico = db.Column(db.String(20), unique=True, nullable=False)
    nome_cepa = db.Column(db.String(50), unique=True, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    genero = db.Column(db.String(100), nullable=False)
    especie = db.Column(db.String(100), nullable=False)
    cepa_strain = db.Column(db.String(100))
    origem = db.Column(db.String(200))
    local_coleta = db.Column(db.String(200))
    data_isolamento = db.Column(db.Date)
    meio_cultivo = db.Column(db.String(100))
    temperatura_cultivo = db.Column(db.String(100))
    metodo_preservacao = db.Column(db.String(100))
    local_armazenamento = db.Column(db.String(200))
    responsavel = db.Column(db.String(100))
    data_cadastro = db.Column(db.Date, default=datetime.utcnow)
    observacoes = db.Column(db.Text)
    publicacoes = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default=STATUS_PUBLIC)
    owner_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    owner = db.relationship("Usuario", backref="registros")

    @property
    def qr_arquivo(self):
        return qr_safe_name(self.nome_cepa)

    def to_dict(self):
        return {
            "id": self.id,
            "codigo_unico": self.codigo_unico,
            "nome_cepa": self.nome_cepa,
            "tipo": self.tipo,
            "genero": self.genero,
            "especie": self.especie,
            "cepa_strain": self.cepa_strain,
            "origem": self.origem,
            "local_coleta": self.local_coleta,
            "data_isolamento": str(self.data_isolamento) if self.data_isolamento else "",
            "meio_cultivo": self.meio_cultivo,
            "temperatura_cultivo": self.temperatura_cultivo,
            "metodo_preservacao": self.metodo_preservacao,
            "local_armazenamento": self.local_armazenamento,
            "responsavel": self.responsavel,
            "data_cadastro": str(self.data_cadastro) if self.data_cadastro else "",
            "observacoes": self.observacoes,
            "publicacoes": self.publicacoes,
            "status": self.status,
        }

    def publicacoes_list(self):
        if not self.publicacoes:
            return []
        result = []
        for line in self.publicacoes.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("arquivo:"):
                val = line[len("arquivo:"):]
                if "|" in val:
                    disk, display = val.split("|", 1)
                else:
                    disk, display = val, val
                result.append({"tipo": "arquivo", "valor": disk, "display": display})
            else:
                result.append({"tipo": "link", "valor": line})
        return result

    @staticmethod
    def serialize_publicacoes(entries):
        lines = []
        for e in entries:
            if e.get("tipo") == "arquivo":
                display = e.get("display") or e["valor"]
                lines.append(f"arquivo:{e['valor']}|{display}")
            elif e.get("valor"):
                lines.append(e["valor"])
        return "\n".join(lines) if lines else None


def formatar_codigo_unico(numero):
    return f"{CODIGO_UNICO_PREFIXO}{numero:0{CODIGO_UNICO_DIGITOS}d}"


def _numero_do_codigo_unico(codigo):
    match = _codigo_unico_re.match(codigo or "")
    return int(match.group(1)) if match else 0


def maior_numero_codigo_unico(session):
    with session.no_autoflush:
        codigos = session.execute(
            select(Colecao.codigo_unico).where(Colecao.codigo_unico.is_not(None))
        ).scalars()
    maior = max((_numero_do_codigo_unico(c) for c in codigos), default=0)
    for pendente in session.new:
        if isinstance(pendente, Colecao) and pendente.codigo_unico:
            maior = max(maior, _numero_do_codigo_unico(pendente.codigo_unico))
    return maior


def backfill_codigo_unico():
    pendentes = (
        db.session.query(Colecao)
        .filter(or_(Colecao.codigo_unico.is_(None), Colecao.codigo_unico == ""))
        .order_by(Colecao.id)
        .all()
    )
    if not pendentes:
        return 0
    numero = maior_numero_codigo_unico(db.session) + 1
    for registro in pendentes:
        registro.codigo_unico = formatar_codigo_unico(numero)
        numero += 1
    db.session.commit()
    return len(pendentes)


@event.listens_for(db.session, "after_attach")
def _atribuir_codigo_unico(session, instance):
    if isinstance(instance, Colecao) and not instance.codigo_unico:
        instance.codigo_unico = formatar_codigo_unico(
            maior_numero_codigo_unico(session) + 1
        )
