from datetime import date

from flask import Blueprint, g, jsonify, request

from .auth import requiere_rol
from .db import get_db

bp = Blueprint("caja", __name__, url_prefix="/caja")


def _reporte(fecha):
    db = get_db()
    resumen = db.execute(
        """SELECT COUNT(*) AS pedidos_pagados, COALESCE(SUM(total), 0) AS total_ventas
           FROM pedidos WHERE estado = 'pagado' AND date(creado_en) = ?""",
        (fecha,),
    ).fetchone()
    por_plato = db.execute(
        """SELECT p.nombre, SUM(pi.cantidad) AS unidades, SUM(pi.cantidad * pi.precio_unitario) AS ventas
           FROM pedido_items pi
           JOIN pedidos pe ON pe.id = pi.pedido_id
           JOIN platos p ON p.id = pi.plato_id
           WHERE pe.estado = 'pagado' AND date(pe.creado_en) = ?
           GROUP BY p.id ORDER BY ventas DESC""",
        (fecha,),
    ).fetchall()
    return {"fecha": fecha, **dict(resumen), "por_plato": [dict(f) for f in por_plato]}


@bp.get("/reporte")
@requiere_rol("administrador")
def reporte_diario():
    return jsonify(_reporte(request.args.get("fecha") or date.today().isoformat()))


@bp.post("/cierre")
@requiere_rol("administrador")
def cerrar_caja():
    fecha = (request.get_json(silent=True) or {}).get("fecha") or date.today().isoformat()
    db = get_db()
    if db.execute("SELECT 1 FROM cierres_caja WHERE fecha = ?", (fecha,)).fetchone():
        return jsonify(error=f"La caja del {fecha} ya fue cerrada"), 409
    pendientes = db.execute(
        "SELECT COUNT(*) FROM pedidos WHERE estado = 'entregado' AND date(creado_en) = ?", (fecha,)
    ).fetchone()[0]
    if pendientes:
        return jsonify(error=f"Hay {pendientes} pedidos entregados sin pagar"), 409

    reporte = _reporte(fecha)
    db.execute(
        "INSERT INTO cierres_caja (fecha, pedidos_pagados, total_ventas, cerrado_por) VALUES (?, ?, ?, ?)",
        (fecha, reporte["pedidos_pagados"], reporte["total_ventas"], g.usuario["id"]),
    )
    db.commit()
    return jsonify(reporte), 201
