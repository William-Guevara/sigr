from flask import Blueprint, g, jsonify, request

from .auth import requiere_rol
from .db import get_db

bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")

# Estados permitidos desde cada estado. Cualquier otro salto se rechaza.
TRANSICIONES = {
    "recibido": {"en_preparacion", "cancelado"},
    "en_preparacion": {"listo"},
    "listo": {"entregado"},
    "entregado": {"pagado"},
    "pagado": set(),
    "cancelado": set(),
}


def _pedido_con_items(pedido_id):
    db = get_db()
    pedido = db.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if pedido is None:
        return None
    items = db.execute(
        """SELECT pi.plato_id, p.nombre, pi.cantidad, pi.precio_unitario
           FROM pedido_items pi JOIN platos p ON p.id = pi.plato_id
           WHERE pi.pedido_id = ?""",
        (pedido_id,),
    ).fetchall()
    return {**dict(pedido), "items": [dict(i) for i in items]}


@bp.post("")
@requiere_rol("mesero", "administrador")
def registrar_pedido():
    datos = request.get_json(silent=True) or {}
    items = datos.get("items") or []
    if not isinstance(datos.get("mesa"), int) or datos["mesa"] <= 0:
        return jsonify(error="La mesa debe ser un entero mayor que cero"), 400
    if not items:
        return jsonify(error="El pedido debe tener al menos un plato"), 400

    db = get_db()
    total = 0
    lineas = []
    for item in items:
        cantidad = item.get("cantidad")
        if not isinstance(cantidad, int) or cantidad <= 0:
            return jsonify(error="Cada plato necesita una cantidad mayor que cero"), 400
        plato = db.execute(
            "SELECT id, precio FROM platos WHERE id = ? AND activo = 1", (item.get("plato_id"),)
        ).fetchone()
        if plato is None:
            return jsonify(error=f"El plato {item.get('plato_id')} no existe o no está en el menú"), 400
        total += plato["precio"] * cantidad
        lineas.append((plato["id"], cantidad, plato["precio"]))

    cursor = db.execute(
        "INSERT INTO pedidos (mesa, registrado_por, total) VALUES (?, ?, ?)",
        (datos["mesa"], g.usuario["id"], total),
    )
    db.executemany(
        "INSERT INTO pedido_items (pedido_id, plato_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)",
        [(cursor.lastrowid, *linea) for linea in lineas],
    )
    db.commit()
    return jsonify(_pedido_con_items(cursor.lastrowid)), 201


@bp.get("")
@requiere_rol("mesero", "administrador")
def listar_pedidos():
    """Seguimiento de pedidos: la vista de cocina y meseros consulta este listado por estado."""
    consulta = "SELECT id, mesa, estado, total, creado_en, actualizado_en FROM pedidos"
    parametros = []
    if request.args.get("estado"):
        consulta += " WHERE estado = ?"
        parametros.append(request.args["estado"])
    filas = get_db().execute(consulta + " ORDER BY creado_en, id", parametros).fetchall()
    return jsonify([dict(f) for f in filas])


@bp.get("/<int:pedido_id>")
@requiere_rol("mesero", "administrador")
def ver_pedido(pedido_id):
    pedido = _pedido_con_items(pedido_id)
    if pedido is None:
        return jsonify(error="Pedido no encontrado"), 404
    return jsonify(pedido)


@bp.patch("/<int:pedido_id>/estado")
@requiere_rol("mesero", "administrador")
def cambiar_estado(pedido_id):
    nuevo = (request.get_json(silent=True) or {}).get("estado")
    db = get_db()
    pedido = db.execute("SELECT estado FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if pedido is None:
        return jsonify(error="Pedido no encontrado"), 404
    if nuevo not in TRANSICIONES.get(pedido["estado"], set()):
        return jsonify(error=f"No se puede pasar de '{pedido['estado']}' a '{nuevo}'"), 409
    db.execute(
        "UPDATE pedidos SET estado = ?, actualizado_en = datetime('now', 'localtime') WHERE id = ?",
        (nuevo, pedido_id),
    )
    db.commit()
    return jsonify(id=pedido_id, estado=nuevo)
