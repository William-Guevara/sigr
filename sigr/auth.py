from functools import wraps

import click
from flask import Blueprint, current_app, g, jsonify, request
from itsdangerous import BadSignature, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")

ROLES = ("cliente", "mesero", "administrador")
TOKEN_MAX_AGE = 8 * 3600  # un turno de trabajo


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="sigr-auth")


def requiere_rol(*roles):
    """Exige un token válido y, si se indican roles, que el usuario tenga uno de ellos."""

    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            cabecera = request.headers.get("Authorization", "")
            if not cabecera.startswith("Bearer "):
                return jsonify(error="Token requerido"), 401
            try:
                datos = _serializer().loads(cabecera[7:], max_age=TOKEN_MAX_AGE)
            except BadSignature:  # incluye SignatureExpired
                return jsonify(error="Token inválido o vencido"), 401
            if roles and datos["rol"] not in roles:
                return jsonify(error="No tiene permiso para esta acción"), 403
            g.usuario = datos
            return vista(*args, **kwargs)

        return envoltura

    return decorador


def crear_usuario(nombre, email, password, rol):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?, ?, ?, ?)",
        (nombre, email.lower(), generate_password_hash(password), rol),
    )
    db.commit()
    return cursor.lastrowid


def _validar_datos_usuario(datos):
    faltantes = [c for c in ("nombre", "email", "password") if not datos.get(c)]
    if faltantes:
        return f"Faltan campos: {', '.join(faltantes)}"
    if len(datos["password"]) < 8:
        return "La contraseña debe tener al menos 8 caracteres"
    if get_db().execute("SELECT 1 FROM usuarios WHERE email = ?", (datos["email"].lower(),)).fetchone():
        return "Ya existe un usuario con ese correo"
    return None


@bp.post("/registro")
def registro():
    """Registro público: siempre crea un cliente."""
    datos = request.get_json(silent=True) or {}
    error = _validar_datos_usuario(datos)
    if error:
        return jsonify(error=error), 400
    usuario_id = crear_usuario(datos["nombre"], datos["email"], datos["password"], "cliente")
    return jsonify(id=usuario_id, rol="cliente"), 201


@bp.post("/usuarios")
@requiere_rol("administrador")
def crear_personal():
    """El administrador crea meseros u otros administradores."""
    datos = request.get_json(silent=True) or {}
    error = _validar_datos_usuario(datos)
    if not error and datos.get("rol") not in ROLES:
        error = f"Rol inválido, use uno de: {', '.join(ROLES)}"
    if error:
        return jsonify(error=error), 400
    usuario_id = crear_usuario(datos["nombre"], datos["email"], datos["password"], datos["rol"])
    return jsonify(id=usuario_id, rol=datos["rol"]), 201


@bp.post("/login")
def login():
    datos = request.get_json(silent=True) or {}
    usuario = get_db().execute(
        "SELECT id, nombre, password_hash, rol FROM usuarios WHERE email = ?",
        (str(datos.get("email", "")).lower(),),
    ).fetchone()
    if usuario is None or not check_password_hash(usuario["password_hash"], datos.get("password", "")):
        return jsonify(error="Credenciales incorrectas"), 401
    token = _serializer().dumps({"id": usuario["id"], "rol": usuario["rol"]})
    return jsonify(token=token, rol=usuario["rol"], nombre=usuario["nombre"])


@bp.cli.command("crear-admin")
@click.argument("email")
@click.password_option()
def crear_admin_command(email, password):
    """Crea el primer administrador del sistema."""
    crear_usuario("Administrador", email, password, "administrador")
    click.echo(f"Administrador {email} creado.")
