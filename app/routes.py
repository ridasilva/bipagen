from functools import wraps
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    abort,
)
from app.models import (
    db,
    Colecao,
    Usuario,
    ROLE_ADMIN,
    ROLE_EDITOR,
    ROLE_VIEWER,
    STATUS_PUBLIC,
    STATUS_PRIVATE,
)
from datetime import datetime

main = Blueprint("main", __name__)


def get_current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return db.session.get(Usuario, user_id)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if user is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)

    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if user is None:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("main.login"))
            if user.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


@main.app_context_processor
def inject_user():
    return {"current_user": get_current_user()}


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if not username or not email or not password:
            flash("Username, email and password are required.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        elif Usuario.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
        elif Usuario.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
        else:
            usuario = Usuario(username=username, email=email, role=ROLE_VIEWER)
            usuario.set_password(password)
            db.session.add(usuario)
            db.session.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("main.login"))
    return render_template("registro.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        usuario = Usuario.query.filter_by(username=username).first()
        if usuario and usuario.check_password(password):
            session["user_id"] = usuario.id
            flash(f"Welcome, {usuario.username}!", "success")
            return redirect(url_for("main.index"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@main.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@main.route("/usuarios")
@role_required(ROLE_ADMIN)
def usuarios():
    usuarios = Usuario.query.order_by(Usuario.id.asc()).all()
    return render_template("usuarios.html", usuarios=usuarios)


@main.route("/usuarios/<int:id>/papel", methods=["POST"])
@role_required(ROLE_ADMIN)
def atualizar_papel(id):
    usuario = db.session.get(Usuario, id)
    if not usuario:
        abort(404)
    novo_papel = request.form.get("role", "")
    if novo_papel not in (ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER):
        flash("Invalid role.", "danger")
        return redirect(url_for("main.usuarios"))
    if usuario.id == get_current_user().id and novo_papel != ROLE_ADMIN:
        flash("You cannot remove your own admin role.", "danger")
        return redirect(url_for("main.usuarios"))
    usuario.role = novo_papel
    db.session.commit()
    flash(f"Role of {usuario.username} updated to {novo_papel}.", "success")
    return redirect(url_for("main.usuarios"))


@main.route("/usuarios/<int:id>/excluir", methods=["POST"])
@role_required(ROLE_ADMIN)
def excluir_usuario(id):
    usuario = db.session.get(Usuario, id)
    if not usuario:
        abort(404)
    if usuario.id == get_current_user().id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("main.usuarios"))
    Colecao.query.filter_by(owner_id=usuario.id).update({Colecao.owner_id: None})
    db.session.delete(usuario)
    db.session.commit()
    flash(f"User {usuario.username} deleted.", "success")
    return redirect(url_for("main.usuarios"))


def visible_query(user):
    if user is None:
        return Colecao.query.filter(Colecao.status == STATUS_PUBLIC)
    if user.is_admin:
        return Colecao.query
    return Colecao.query.filter(
        db.or_(Colecao.status == STATUS_PUBLIC, Colecao.owner_id == user.id)
    )


def can_view_registro(registro, user):
    if registro.status == STATUS_PUBLIC:
        return True
    if user is None:
        return False
    return user.is_admin or registro.owner_id == user.id


@main.route("/colecao")
def listar():
    search = request.args.get("search", "")
    page = request.args.get("page", 1, type=int)
    per_page = 20
    query = visible_query(get_current_user())
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
@role_required(ROLE_ADMIN, ROLE_EDITOR)
def novo():
    user = get_current_user()
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
            status = (
                request.form.get("status", STATUS_PUBLIC)
                if request.form.get("status") in (STATUS_PUBLIC, STATUS_PRIVATE)
                else STATUS_PUBLIC
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
                status=status,
                owner_id=user.id,
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
@role_required(ROLE_ADMIN, ROLE_EDITOR)
def editar(id):
    user = get_current_user()
    registro = Colecao.query.get_or_404(id)
    if not user.is_admin and registro.owner_id != user.id:
        abort(403)
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
            status = request.form.get("status")
            if status in (STATUS_PUBLIC, STATUS_PRIVATE):
                registro.status = status
            db.session.commit()
            flash("Record updated successfully!", "success")
            return redirect(url_for("main.listar"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")
    return render_template("form.html", registro=registro)


@main.route("/colecao/excluir/<int:id>", methods=["POST"])
@role_required(ROLE_ADMIN)
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
    user = get_current_user()
    if not can_view_registro(registro, user):
        abort(403)
    return render_template("detalhe.html", registro=registro)


@main.route("/servicos", methods=["GET", "POST"])
def servicos():
    categorias = [
        {"id": 1, "nome": "Category 1 — Basic Strains", "preco_publico": 200, "preco_privado": 400},
        {"id": 2, "nome": "Category 2 — Standard Strains", "preco_publico": 300, "preco_privado": 600},
        {"id": 3, "nome": "Category 3 — Specialized Strains", "preco_publico": 500, "preco_privado": 1000},
        {"id": 4, "nome": "Category 4 — Premium Strains", "preco_publico": 1050, "preco_privado": 2100},
    ]
    return render_template("servicos.html", categorias=categorias)
