"""Pruebas básicas de integración: recorren los cinco módulos de la línea base a través de la API."""

import os
import tempfile
import unittest
from datetime import date

from sigr import create_app, db
from sigr.auth import crear_usuario

CLAVE = "clave-segura-123"


class IntegracionSIGR(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "DATABASE": os.path.join(self.tmp.name, "test.db")})
        with self.app.app_context():
            db.init_db()
            crear_usuario("Admin", "admin@sigr.co", CLAVE, "administrador")
        self.client = self.app.test_client()
        self.admin = self._login("admin@sigr.co")
        self._post("/auth/usuarios", self.admin,
                   {"nombre": "Mesero", "email": "mesero@sigr.co", "password": CLAVE, "rol": "mesero"})
        self.mesero = self._login("mesero@sigr.co")

    def tearDown(self):
        self.tmp.cleanup()

    # --- utilidades ---
    def _login(self, email):
        respuesta = self.client.post("/auth/login", json={"email": email, "password": CLAVE})
        self.assertEqual(respuesta.status_code, 200)
        return {"Authorization": f"Bearer {respuesta.json['token']}"}

    def _post(self, url, headers, datos):
        return self.client.post(url, json=datos, headers=headers)

    def _crear_plato(self, nombre="Bandeja paisa", precio=32000):
        categoria = self._post("/menu/categorias", self.admin, {"nombre": "Platos fuertes"})
        categoria_id = categoria.json["id"] if categoria.status_code == 201 else 1
        respuesta = self._post("/menu/platos", self.admin,
                               {"categoria_id": categoria_id, "nombre": nombre, "precio": precio})
        self.assertEqual(respuesta.status_code, 201)
        return respuesta.json["id"]

    # --- autenticación ---
    def test_salud(self):
        self.assertEqual(self.client.get("/salud").json["estado"], "ok")

    def test_registro_publico_crea_solo_clientes(self):
        respuesta = self.client.post("/auth/registro", json={
            "nombre": "Ana", "email": "ana@correo.co", "password": CLAVE, "rol": "administrador"})
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json["rol"], "cliente")

    def test_login_con_clave_incorrecta(self):
        respuesta = self.client.post("/auth/login", json={"email": "admin@sigr.co", "password": "otra"})
        self.assertEqual(respuesta.status_code, 401)

    def test_rutas_protegidas_por_rol(self):
        self.assertEqual(self.client.post("/menu/categorias", json={"nombre": "X"}).status_code, 401)
        self.assertEqual(self._post("/menu/categorias", self.mesero, {"nombre": "X"}).status_code, 403)

    # --- menú ---
    def test_crud_de_platos(self):
        plato_id = self._crear_plato()
        self.assertEqual(len(self.client.get("/menu/platos").json), 1)
        actualizado = self.client.put(f"/menu/platos/{plato_id}", headers=self.admin,
                                      json={"categoria_id": 1, "nombre": "Bandeja paisa", "precio": 34000})
        self.assertEqual(actualizado.status_code, 200)
        self.assertEqual(self.client.get("/menu/platos").json[0]["precio"], 34000)
        self.assertEqual(self.client.delete(f"/menu/platos/{plato_id}", headers=self.admin).status_code, 204)
        self.assertEqual(self.client.get("/menu/platos").json, [])

    # --- pedidos ---
    def test_flujo_completo_de_un_pedido(self):
        plato_id = self._crear_plato(precio=20000)
        pedido = self._post("/pedidos", self.mesero, {"mesa": 4, "items": [{"plato_id": plato_id, "cantidad": 2}]})
        self.assertEqual(pedido.status_code, 201)
        self.assertEqual(pedido.json["total"], 40000)
        pedido_id = pedido.json["id"]
        for estado in ("en_preparacion", "listo", "entregado", "pagado"):
            respuesta = self.client.patch(f"/pedidos/{pedido_id}/estado", headers=self.mesero, json={"estado": estado})
            self.assertEqual(respuesta.status_code, 200, estado)
        self.assertEqual(self.client.get("/pedidos?estado=pagado", headers=self.mesero).json[0]["id"], pedido_id)

    def test_pedido_no_salta_estados(self):
        plato_id = self._crear_plato()
        pedido_id = self._post("/pedidos", self.mesero,
                               {"mesa": 1, "items": [{"plato_id": plato_id, "cantidad": 1}]}).json["id"]
        respuesta = self.client.patch(f"/pedidos/{pedido_id}/estado", headers=self.mesero, json={"estado": "pagado"})
        self.assertEqual(respuesta.status_code, 409)

    # --- reservas ---
    def test_no_permite_reservar_mesa_ocupada(self):
        reserva = {"fecha": "2026-12-24", "hora": "19:00", "personas": 4, "mesa": 2}
        self.assertEqual(self._post("/reservas", self.mesero, reserva).status_code, 201)
        self.assertEqual(self._post("/reservas", self.mesero, {**reserva, "hora": "20:00"}).status_code, 409)
        self.assertEqual(self._post("/reservas", self.mesero, {**reserva, "hora": "21:00"}).status_code, 201)
        self.assertEqual(len(self.client.get("/reservas?fecha=2026-12-24", headers=self.mesero).json), 2)

    # --- caja ---
    def test_cierre_de_caja_del_dia(self):
        plato_id = self._crear_plato(precio=15000)
        pedido_id = self._post("/pedidos", self.mesero,
                               {"mesa": 3, "items": [{"plato_id": plato_id, "cantidad": 3}]}).json["id"]
        for estado in ("en_preparacion", "listo", "entregado", "pagado"):
            self.client.patch(f"/pedidos/{pedido_id}/estado", headers=self.mesero, json={"estado": estado})
        hoy = date.today().isoformat()
        cierre = self._post("/caja/cierre", self.admin, {"fecha": hoy})
        self.assertEqual(cierre.status_code, 201)
        self.assertEqual(cierre.json["total_ventas"], 45000)
        self.assertEqual(self._post("/caja/cierre", self.admin, {"fecha": hoy}).status_code, 409)


if __name__ == "__main__":
    unittest.main()
