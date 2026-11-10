-- Esquema de base de datos del SIGR (SQLite)
-- Montos en pesos colombianos, como enteros.

DROP TABLE IF EXISTS cierres_caja;
DROP TABLE IF EXISTS reservas;
DROP TABLE IF EXISTS pedido_items;
DROP TABLE IF EXISTS pedidos;
DROP TABLE IF EXISTS platos;
DROP TABLE IF EXISTS categorias;
DROP TABLE IF EXISTS usuarios;

CREATE TABLE usuarios (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    rol           TEXT    NOT NULL CHECK (rol IN ('cliente', 'mesero', 'administrador')),
    creado_en     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE categorias (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT    NOT NULL UNIQUE
);

CREATE TABLE platos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id INTEGER NOT NULL REFERENCES categorias (id),
    nombre       TEXT    NOT NULL,
    descripcion  TEXT,
    precio       INTEGER NOT NULL CHECK (precio > 0),
    activo       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE pedidos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    mesa           INTEGER NOT NULL,
    registrado_por INTEGER NOT NULL REFERENCES usuarios (id),
    estado         TEXT    NOT NULL DEFAULT 'recibido'
                   CHECK (estado IN ('recibido', 'en_preparacion', 'listo', 'entregado', 'pagado', 'cancelado')),
    total          INTEGER NOT NULL,
    creado_en      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    actualizado_en TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE pedido_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id       INTEGER NOT NULL REFERENCES pedidos (id) ON DELETE CASCADE,
    plato_id        INTEGER NOT NULL REFERENCES platos (id),
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario INTEGER NOT NULL
);

CREATE TABLE reservas (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL REFERENCES usuarios (id),
    fecha      TEXT    NOT NULL,
    hora       TEXT    NOT NULL,
    personas   INTEGER NOT NULL CHECK (personas BETWEEN 1 AND 20),
    mesa       INTEGER NOT NULL,
    estado     TEXT    NOT NULL DEFAULT 'confirmada' CHECK (estado IN ('confirmada', 'cancelada')),
    creado_en  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE cierres_caja (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha           TEXT    NOT NULL UNIQUE,
    pedidos_pagados INTEGER NOT NULL,
    total_ventas    INTEGER NOT NULL,
    cerrado_por     INTEGER NOT NULL REFERENCES usuarios (id),
    creado_en       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);
