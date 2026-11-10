# Manual de despliegue (entorno de pruebas)

## 1. Preparar el entorno

```bash
git clone https://github.com/<usuario>/sigr.git
cd sigr
git checkout v1.0.0              # desplegar siempre desde un tag, no desde una rama
python -m venv .venv
.venv\Scripts\activate           # Linux o macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Variables de entorno

| Variable | Uso | Valor por defecto |
|---|---|---|
| `SIGR_SECRET_KEY` | Firma de los tokens de sesión | `dev-cambiar-en-produccion` (solo desarrollo) |
| `SIGR_DATABASE` | Ruta del archivo SQLite | `sigr.db` |

Fuera de desarrollo, `SIGR_SECRET_KEY` siempre debe definirse con un valor largo y aleatorio.

## 3. Base de datos y primer administrador

```bash
flask --app sigr init-db                                # crea las tablas (borra datos existentes)
flask --app sigr auth crear-admin admin@restaurante.co  # pide la contraseña por consola
```

## 4. Verificar antes de levantar

```bash
python -m unittest discover -s tests -t .
```

Si alguna prueba falla, no se despliega.

## 5. Ejecutar

```bash
flask --app sigr run --host 0.0.0.0 --port 5000
```

Comprobación: `GET http://<servidor>:5000/salud` debe responder `{"estado": "ok", "version": "1.0.0"}`.

El servidor de Flask sirve para pruebas. Para producción se usaría un servidor WSGI (por ejemplo, Gunicorn o Waitress) y una base de datos de servidor. Ese cambio queda fuera de esta línea base.
