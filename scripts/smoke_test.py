"""Prueba de humo contra un ambiente desplegado (staging).

Recorre el flujo crítico del restaurante por la API real: salud, login,
menú, pedido con cambio de estado y reserva. Si un paso falla, termina con
código 1 y el pipeline se detiene.

Uso: python scripts/smoke_test.py http://localhost:8000
Variables: SIGR_ADMIN_EMAIL y SIGR_ADMIN_PASSWORD (administrador creado en
el despliegue).
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

URL_DEFECTO = "http://localhost:8000"
BASE = (sys.argv[1] if len(sys.argv) > 1 else URL_DEFECTO).rstrip("/")
EMAIL = os.environ.get("SIGR_ADMIN_EMAIL", "admin@sigr.co")
CLAVE = os.environ.get("SIGR_ADMIN_PASSWORD", "")


def llamar(metodo, ruta, datos=None, token=None):
    cuerpo = json.dumps(datos).encode() if datos is not None else None
    peticion = urllib.request.Request(BASE + ruta, data=cuerpo, method=metodo)
    peticion.add_header("Content-Type", "application/json")
    if token:
        peticion.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(peticion, timeout=5) as respuesta:
            texto = respuesta.read().decode()
            return respuesta.status, json.loads(texto) if texto else None
    except urllib.error.HTTPError as error:
        return error.code, None


def verificar(descripcion, condicion):
    print(("[OK]   " if condicion else "[FALLA] ") + descripcion)
    if not condicion:
        sys.exit(1)


def esperar_servicio(intentos=15):
    for _ in range(intentos):
        try:
            if llamar("GET", "/salud")[0] == 200:
                return True
        except urllib.error.URLError:
            pass
        time.sleep(2)
    return False


def main():
    verificar(f"El servicio responde en {BASE}", esperar_servicio())
    estado, salud = llamar("GET", "/salud")
    verificar(f"/salud -> {salud}", estado == 200 and salud["estado"] == "ok")

    estado, _ = llamar("POST", "/auth/login",
                       {"email": EMAIL, "password": "clave-equivocada"})
    verificar("Login con clave incorrecta es rechazado (401)", estado == 401)

    estado, sesion = llamar("POST", "/auth/login",
                            {"email": EMAIL, "password": CLAVE})
    verificar("Login del administrador", estado == 200)
    token = sesion["token"]

    estado, categoria = llamar("POST", "/menu/categorias",
                               {"nombre": "Platos fuertes"}, token)
    verificar("Crear categoría del menú", estado == 201)
    estado, plato = llamar("POST", "/menu/platos", {
        "categoria_id": categoria["id"], "nombre": "Ajiaco",
        "precio": 28000}, token)
    verificar("Crear plato del menú", estado == 201)

    estado, pedido = llamar("POST", "/pedidos", {
        "mesa": 5, "items": [{"plato_id": plato["id"], "cantidad": 2}]},
        token)
    verificar(f"Registrar pedido (total {pedido and pedido['total']})",
              estado == 201 and pedido["total"] == 56000)
    estado, _ = llamar("PATCH", f"/pedidos/{pedido['id']}/estado",
                       {"estado": "en_preparacion"}, token)
    verificar("Pedido pasa a 'en_preparacion'", estado == 200)

    reserva = {"fecha": "2030-12-24", "hora": "19:00",
               "personas": 4, "mesa": 2}
    estado, _ = llamar("POST", "/reservas", reserva, token)
    verificar("Crear reserva", estado == 201)
    estado, _ = llamar("POST", "/reservas", reserva, token)
    verificar("Reserva cruzada en la misma mesa es rechazada (409)",
              estado == 409)

    print("Prueba de humo superada.")


if __name__ == "__main__":
    main()
