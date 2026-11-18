"""Prueba de carga básica contra staging (requisito no funcional).

Lanza peticiones concurrentes a las rutas de lectura más usadas y falla si
hay errores o si el percentil 95 del tiempo de respuesta supera el umbral.

Uso: python scripts/prueba_carga.py http://localhost:8000
Variables opcionales: CARGA_PETICIONES (300), CARGA_USUARIOS (20),
CARGA_P95_MS (500).
"""

import os
import statistics
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

URL_DEFECTO = "http://localhost:8000"
BASE = (sys.argv[1] if len(sys.argv) > 1 else URL_DEFECTO).rstrip("/")
PETICIONES = int(os.environ.get("CARGA_PETICIONES", 300))
USUARIOS = int(os.environ.get("CARGA_USUARIOS", 20))
UMBRAL_P95_MS = float(os.environ.get("CARGA_P95_MS", 500))
RUTAS = ["/salud", "/menu/platos", "/menu/categorias"]


def una_peticion(numero):
    ruta = RUTAS[numero % len(RUTAS)]
    inicio = time.perf_counter()
    try:
        with urllib.request.urlopen(BASE + ruta, timeout=5) as respuesta:
            ok = respuesta.status == 200
    except Exception:
        ok = False
    return ok, (time.perf_counter() - inicio) * 1000


def main():
    inicio = time.perf_counter()
    with ThreadPoolExecutor(max_workers=USUARIOS) as hilos:
        resultados = list(hilos.map(una_peticion, range(PETICIONES)))
    duracion = time.perf_counter() - inicio

    tiempos = sorted(ms for _, ms in resultados)
    errores = sum(1 for ok, _ in resultados if not ok)
    p95 = tiempos[int(len(tiempos) * 0.95) - 1]
    resumen = (
        f"Peticiones: {PETICIONES} | Usuarios concurrentes: {USUARIOS}\n"
        f"Errores: {errores} | Rendimiento: {PETICIONES / duracion:.1f} "
        f"peticiones/s\n"
        f"Promedio: {statistics.mean(tiempos):.1f} ms | "
        f"p95: {p95:.1f} ms (umbral {UMBRAL_P95_MS:.0f} ms)"
    )
    print(resumen)

    resumen_ci = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumen_ci:
        with open(resumen_ci, "a", encoding="utf-8") as archivo:
            archivo.write("### Prueba de carga en staging\n```\n")
            archivo.write(resumen + "\n```\n")

    if errores or p95 > UMBRAL_P95_MS:
        print("[FALLA] No cumple el requisito de rendimiento.")
        sys.exit(1)
    print("[OK] Cumple el requisito de rendimiento.")


if __name__ == "__main__":
    main()
