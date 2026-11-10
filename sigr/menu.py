from flask import Blueprint, jsonify, request

from .auth import requiere_rol
from .db import get_db

bp = Blueprint("menu", __name__, url_prefix="/menu")


@bp.get("/categorias")
def listar_categorias():
    filas = get_db().execute("SELECT id, nombre FROM categorias ORDER BY nombre").fetchall()
    return jsonify([dict(f) for f in filas])


@bp.post("/categorias")
@requiere_rol("administrador")
def crear_categoria():
    nombre = ((request.get_json(silent=True) or {}).get("nombre") or "").strip()
    if not nombre:
        return jsonify(error="El nombre es obligatorio"), 400
    db = get_db()
    if db.execute("SELECT 1 FROM categorias WHERE nombre = ?", (nombre,)).fetchone():
        return jsonify(error="La categoría ya existe"), 409
    cursor = db.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
    db.commit()
    return jsonify(id=cursor.lastrowid, nombre=nombre), 201


@bp.put("/categorias/<int:categoria_id>")
@requiere_rol("administrador")
def renombrar_categoria(categoria_id):
    nombre = ((request.get_json(silent=True) or {}).get("nombre") or "").strip()
    if not nombre:
        return jsonify(error="El nombre es obligatorio"), 400
    db = get_db()
    repetida = db.execute(
        "SELECT 1 FROM categorias WHERE nombre = ? AND id <> ?", (nombre, categoria_id)
    ).fetchone()
    if repetida:
        return jsonify(error="La categoría ya existe"), 409
    cursor = db.execute("UPDATE categorias SET nombre = ? WHERE id = ?", (nombre, categoria_id))
    db.commit()
    if cursor.rowcount == 0:
        return jsonify(error="Categoría no encontrada"), 404
    return jsonify(id=categoria_id, nombre=nombre)


@bp.delete("/categorias/<int:categoria_id>")
@requiere_rol("administrador")
def eliminar_categoria(categoria_id):
    """Solo se elimina una categoría sin platos, para no dejar platos huérfanos."""
    db = get_db()
    if db.execute("SELECT 1 FROM platos WHERE categoria_id = ?", (categoria_id,)).fetchone():
        return jsonify(error="La categoría tiene platos asociados"), 409
    cursor = db.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))
    db.commit()
    if cursor.rowcount == 0:
        return jsonify(error="Categoría no encontrada"), 404
    return "", 204


@bp.get("/platos")
def listar_platos():
    """Menú digital: solo platos activos, opcionalmente filtrados por categoría."""
    consulta = "SELECT id, categoria_id, nombre, descripcion, precio FROM platos WHERE activo = 1"
    parametros = []
    if request.args.get("categoria_id"):
        consulta += " AND categoria_id = ?"
        parametros.append(request.args["categoria_id"])
    filas = get_db().execute(consulta + " ORDER BY nombre", parametros).fetchall()
    return jsonify([dict(f) for f in filas])


def _validar_plato(datos):
    if not (datos.get("nombre") or "").strip():
        return "El nombre es obligatorio"
    precio = datos.get("precio")
    if not isinstance(precio, int) or isinstance(precio, bool) or precio <= 0:
        return "El precio debe ser un entero mayor que cero"
    if not get_db().execute("SELECT 1 FROM categorias WHERE id = ?", (datos.get("categoria_id"),)).fetchone():
        return "La categoría no existe"
    return None


@bp.post("/platos")
@requiere_rol("administrador")
def crear_plato():
    datos = request.get_json(silent=True) or {}
    error = _validar_plato(datos)
    if error:
        return jsonify(error=error), 400
    db = get_db()
    cursor = db.execute(
        "INSERT INTO platos (categoria_id, nombre, descripcion, precio) VALUES (?, ?, ?, ?)",
        (datos["categoria_id"], datos["nombre"].strip(), datos.get("descripcion"), datos["precio"]),
    )
    db.commit()
    return jsonify(id=cursor.lastrowid), 201


@bp.put("/platos/<int:plato_id>")
@requiere_rol("administrador")
def actualizar_plato(plato_id):
    datos = request.get_json(silent=True) or {}
    error = _validar_plato(datos)
    if error:
        return jsonify(error=error), 400
    db = get_db()
    cursor = db.execute(
        "UPDATE platos SET categoria_id = ?, nombre = ?, descripcion = ?, precio = ? WHERE id = ? AND activo = 1",
        (datos["categoria_id"], datos["nombre"].strip(), datos.get("descripcion"), datos["precio"], plato_id),
    )
    db.commit()
    if cursor.rowcount == 0:
        return jsonify(error="Plato no encontrado"), 404
    return jsonify(id=plato_id)


@bp.delete("/platos/<int:plato_id>")
@requiere_rol("administrador")
def eliminar_plato(plato_id):
    """Baja lógica: el plato sale del menú pero se conserva para los pedidos históricos."""
    db = get_db()
    cursor = db.execute("UPDATE platos SET activo = 0 WHERE id = ? AND activo = 1", (plato_id,))
    db.commit()
    if cursor.rowcount == 0:
        return jsonify(error="Plato no encontrado"), 404
    return "", 204
