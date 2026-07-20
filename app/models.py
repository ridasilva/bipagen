from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Colecao(db.Model):
    __tablename__ = "colecao_microrganismos_qr"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_acesso = db.Column(db.String(50), unique=True, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    genero = db.Column(db.String(100), nullable=False)
    especie = db.Column(db.String(100), nullable=False)
    cepa_strain = db.Column(db.String(100))
    origem_isolamento = db.Column(db.String(200))
    local_coleta = db.Column(db.String(200))
    data_isolamento = db.Column(db.Date)
    meio_cultivo = db.Column(db.String(100))
    metodo_preservacao = db.Column(db.String(100))
    local_armazenamento = db.Column(db.String(200))
    responsavel = db.Column(db.String(100))
    data_cadastro = db.Column(db.Date, default=datetime.utcnow)
    observacoes = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "codigo_acesso": self.codigo_acesso,
            "tipo": self.tipo,
            "genero": self.genero,
            "especie": self.especie,
            "cepa_strain": self.cepa_strain,
            "origem_isolamento": self.origem_isolamento,
            "local_coleta": self.local_coleta,
            "data_isolamento": str(self.data_isolamento) if self.data_isolamento else "",
            "meio_cultivo": self.meio_cultivo,
            "metodo_preservacao": self.metodo_preservacao,
            "local_armazenamento": self.local_armazenamento,
            "responsavel": self.responsavel,
            "data_cadastro": str(self.data_cadastro) if self.data_cadastro else "",
            "observacoes": self.observacoes,
        }
