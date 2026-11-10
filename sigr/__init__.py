import os

import click
from flask import Flask, jsonify

from . import auth, db, menu, pedidos, reservas

__version__ = "0.1.0"


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SIGR_SECRET_KEY", "dev-cambiar-en-produccion"),
        DATABASE=os.environ.get("SIGR_DATABASE", "sigr.db"),
    )
    if config:
        app.config.update(config)

    app.teardown_appcontext(db.close_db)
    for blueprint in (auth.bp, menu.bp, pedidos.bp, reservas.bp):
        app.register_blueprint(blueprint)

    @app.cli.command("init-db")
    def init_db_command():
        """Crea las tablas desde db/schema.sql (borra los datos existentes)."""
        db.init_db()
        click.echo("Base de datos inicializada.")

    @app.get("/salud")
    def salud():
        return jsonify(estado="ok", version=__version__)

    return app
