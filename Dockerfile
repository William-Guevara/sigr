# Imagen del SIGR para los ambientes de staging y producción.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SIGR_DATABASE=/datos/sigr.db

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==26.2.0

COPY sigr ./sigr
COPY db ./db

# La aplicación no corre como root.
RUN useradd --create-home sigr && mkdir /datos && chown sigr /datos
USER sigr

EXPOSE 8000

# Docker marca el contenedor como "unhealthy" si /salud deja de responder.
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/salud', timeout=2)"

# init-db crea las tablas si es un ambiente nuevo. En staging la base se
# recrea en cada despliegue; en producción se montaría un volumen persistente
# y este paso se haría una sola vez.
CMD ["sh", "-c", "flask --app sigr init-db && exec gunicorn --bind 0.0.0.0:8000 --workers 2 'sigr:create_app()'"]
