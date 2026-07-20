from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, Colecao
from datetime import datetime

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/colecao")
def listar():
    search = request.args.get("search", "")
    page = request.args.get("page", 1, type=int)
    per_page = 20
    query = Colecao.query
    if search:
        query = query.filter(
            db.or_(
                Colecao.codigo_acesso.ilike(f"%{search}%"),
                Colecao.genero.ilike(f"%{search}%"),
                Colecao.especie.ilike(f"%{search}%"),
                Colecao.tipo.ilike(f"%{search}%"),
                Colecao.responsavel.ilike(f"%{search}%"),
            )
        )
    pagination = query.order_by(Colecao.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    registros = pagination.items
    return render_template(
        "listar.html", registros=registros, pagination=pagination, search=search
    )


@main.route("/colecao/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        try:
            data_isol = (
                datetime.strptime(request.form["data_isolamento"], "%Y-%m-%d").date()
                if request.form.get("data_isolamento")
                else None
            )
            data_cad = (
                datetime.strptime(request.form["data_cadastro"], "%Y-%m-%d").date()
                if request.form.get("data_cadastro")
                else datetime.utcnow().date()
            )
            registro = Colecao(
                codigo_acesso=request.form["codigo_acesso"],
                tipo=request.form["tipo"],
                genero=request.form["genero"],
                especie=request.form["especie"],
                cepa_strain=request.form.get("cepa_strain"),
                origem_isolamento=request.form.get("origem_isolamento"),
                local_coleta=request.form.get("local_coleta"),
                data_isolamento=data_isol,
                meio_cultivo=request.form.get("meio_cultivo"),
                metodo_preservacao=request.form.get("metodo_preservacao"),
                local_armazenamento=request.form.get("local_armazenamento"),
                responsavel=request.form.get("responsavel"),
                data_cadastro=data_cad,
                observacoes=request.form.get("observacoes"),
            )
            db.session.add(registro)
            db.session.commit()
            flash("Record added successfully!", "success")
            return redirect(url_for("main.listar"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")
    return render_template("form.html", registro=None)


@main.route("/colecao/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    registro = Colecao.query.get_or_404(id)
    if request.method == "POST":
        try:
            registro.codigo_acesso = request.form["codigo_acesso"]
            registro.tipo = request.form["tipo"]
            registro.genero = request.form["genero"]
            registro.especie = request.form["especie"]
            registro.cepa_strain = request.form.get("cepa_strain")
            registro.origem_isolamento = request.form.get("origem_isolamento")
            registro.local_coleta = request.form.get("local_coleta")
            registro.data_isolamento = (
                datetime.strptime(request.form["data_isolamento"], "%Y-%m-%d").date()
                if request.form.get("data_isolamento")
                else None
            )
            registro.meio_cultivo = request.form.get("meio_cultivo")
            registro.metodo_preservacao = request.form.get("metodo_preservacao")
            registro.local_armazenamento = request.form.get("local_armazenamento")
            registro.responsavel = request.form.get("responsavel")
            registro.data_cadastro = (
                datetime.strptime(request.form["data_cadastro"], "%Y-%m-%d").date()
                if request.form.get("data_cadastro")
                else registro.data_cadastro
            )
            registro.observacoes = request.form.get("observacoes")
            db.session.commit()
            flash("Record updated successfully!", "success")
            return redirect(url_for("main.listar"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")
    return render_template("form.html", registro=registro)


@main.route("/colecao/excluir/<int:id>", methods=["POST"])
def excluir(id):
    registro = Colecao.query.get_or_404(id)
    try:
        db.session.delete(registro)
        db.session.commit()
        flash("Record deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {e}", "danger")
    return redirect(url_for("main.listar"))


@main.route("/colecao/<int:id>")
def detalhe(id):
    registro = Colecao.query.get_or_404(id)
    return render_template("detalhe.html", registro=registro)
