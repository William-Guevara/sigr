# SIGR – Sistema Integral de Gestión de Restaurante

API web para gestionar la operación de un restaurante: usuarios, menú digital, pedidos, reservas y cierre de caja.

Esta versión (`v1.0.0`) es la **línea base del código fuente**. Es el primer punto estable del proyecto, y desde aquí cualquier cambio entra por solicitud de cambio (issue), rama propia y pull request.

## Módulos de la línea base

| Módulo | Archivo | Qué hace |
|---|---|---|
| Autenticación | `sigr/auth.py` | Registro, login con token y permisos por rol (cliente, mesero, administrador) |
| Menú digital | `sigr/menu.py` | CRUD de categorías y platos |
| Pedidos | `sigr/pedidos.py` | Registro de pedidos por mesa y seguimiento por estados |
| Reservas | `sigr/reservas.py` | Reservas por fecha y hora, sin cruces en la misma mesa |
| Caja | `sigr/caja.py` | Reporte de ventas del día y cierre de caja |

## Requisitos

- Python 3.11 o superior
- Las dependencias de `requirements.txt` (solo Flask)

## Cómo clonarlo y ejecutarlo

```bash
git clone https://github.com/<usuario>/sigr.git
cd sigr
python -m venv .venv
.venv\Scripts\activate          # en Linux o macOS: source .venv/bin/activate
pip install -r requirements.txt
flask --app sigr init-db
flask --app sigr auth crear-admin admin@restaurante.co
flask --app sigr run
```

La API queda en `http://127.0.0.1:5000`. Para comprobar que responde: `GET /salud`.

## Pruebas

```bash
python -m unittest discover -s tests -t . -v
```

## Estructura del repositorio

```
sigr/
├── sigr/                  # código de la aplicación (un archivo por módulo)
├── db/schema.sql          # esquema de la base de datos
├── tests/                 # pruebas de integración
├── docs/
│   ├── estructura_bd.md   # descripción de tablas y relaciones
│   └── manual_despliegue.md
├── CHANGELOG.md
├── LICENSE.txt
└── requirements.txt
```

## Convenciones

- Rama estable: `main`. Ningún cambio llega a `main` sin pull request.
- Ramas de trabajo: `feature/<tema>`, `fix/<tema>`, `hotfix/<tema>`.
- Commits con prefijo de tipo: `feat`, `fix`, `test`, `docs`, `chore`.
- Versionado semántico; cada versión estable se marca con un tag anotado (`v1.0.0`, `v1.1.0`, ...).
- Código en español para los nombres de dominio (pedido, reserva, plato), siguiendo PEP 8.

## Licencia

MIT. Ver `LICENSE.txt`.
