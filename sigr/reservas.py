from datetime import datetime

from flask import Blueprint, g, jsonify, request

from .auth import requiere_rol
from .db import get_db

bp = Blueprint("reservas", __name__, url_prefix="/reservas")

DURACION_MINUTOS = 120  # tiempo que una reserva ocupa la mesa


def _minutos(hora):
    h, m = hora.split(":")
    return int(h) * 60 + int(m)


@bp.post("")
@requiere_rol("cliente", "mesero", "administrador")
def crear_reserva():
    datos = request.get_json(silent=True) or {}
    try:
        datetime.strptime(datos.get("fecha", ""), "%Y-%m-%d")
        datetime.strptime(datos.get("hora", ""), "%H:%M")
    except ValueError:
        return jsonify(error="Use fecha AAAA-MM-DD y hora HH:MM"), 400
    personas, mesa = datos.get("personas"), datos.get("mesa")
    if not isinstance(personas, int) or not 1 <= personas <= 20:
        return jsonify(error="Las personas deben estar entre 1 y 20"), 400
    if not isinstance(mesa, int) or mesa <= 0:
        return jsonify(error="La mesa debe ser un entero mayor que cero"), 400

    db = get_db()
    ocupadas = db.execute(
        "SELECT hora FROM reservas WHERE mesa = ? AND fecha = ? AND estado = 'confirmada'",
        (mesa, datos["fecha"]),
    ).fetchall()
    inicio = _minutos(datos["hora"])
    if any(abs(_minutos(r["hora"]) - inicio) < DURACION_MINUTOS for r in ocupadas):
        return jsonify(error="La mesa ya está reservada en esa franja"), 409

    cursor = db.execute(
        "INSERT INTO reservas (cliente_id, fecha, hora, personas, mesa) VALUES (?, ?, ?, ?, ?)",
        (g.usuario["id"], datos["fecha"], datos["hora"], personas, mesa),
    )
    db.commit()
    return jsonify(id=cursor.lastrowid, estado="confirmada"), 201


@bp.get("")
@requiere_rol("mesero", "administrador")
def listar_reservas():
    fecha = request.args.get("fecha")
    if not fecha:
        return jsonify(error="Indique la fecha a consultar"), 400
    filas = get_db().execute(
        "SELECT id, fecha, hora, personas, mesa, estado FROM reservas WHERE fecha = ? ORDER BY hora, mesa",
        (fecha,),
    ).fetchall()
    return jsonify([dict(f) for f in filas])


@bp.delete("/<int:reserva_id>")
@requiere_rol("cliente", "mesero", "administrador")
def cancelar_reserva(reserva_id):
    db = get_db()
    reserva = db.execute("SELECT cliente_id, estado FROM reservas WHERE id = ?", (reserva_id,)).fetchone()
    if reserva is None or reserva["estado"] != "confirmada":
        return jsonify(error="Reserva no encontrada o ya cancelada"), 404
    if g.usuario["rol"] == "cliente" and reserva["cliente_id"] != g.usuario["id"]:
        return jsonify(error="Solo puede cancelar sus propias reservas"), 403
    db.execute("UPDATE reservas SET estado = 'cancelada' WHERE id = ?", (reserva_id,))
    db.commit()
    return "", 204
