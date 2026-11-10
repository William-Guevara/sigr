# Estructura de la base de datos

Motor: SQLite (archivo `sigr.db`). El esquema completo está en `db/schema.sql`. Los montos se guardan en pesos colombianos como enteros.

```
usuarios 1──* pedidos 1──* pedido_items *──1 platos *──1 categorias
usuarios 1──* reservas
usuarios 1──* cierres_caja
```

| Tabla | Para qué sirve | Campos clave |
|---|---|---|
| `usuarios` | Clientes, meseros y administradores | `email` único, `password_hash`, `rol` |
| `categorias` | Agrupan los platos del menú | `nombre` único |
| `platos` | Menú digital | `categoria_id`, `precio`, `activo` (baja lógica) |
| `pedidos` | Pedido por mesa | `mesa`, `estado`, `total`, `registrado_por` |
| `pedido_items` | Platos de cada pedido | `cantidad`, `precio_unitario` (precio al momento del pedido) |
| `reservas` | Reserva de mesa | `fecha`, `hora`, `personas` (1 a 20), `mesa`, `estado` |
| `cierres_caja` | Un cierre por día | `fecha` única, `pedidos_pagados`, `total_ventas` |

## Estados de un pedido

```
recibido → en_preparacion → listo → entregado → pagado
    └──→ cancelado
```

Cualquier otro salto se rechaza con código 409.

## Decisiones de diseño

- **Precio copiado en `pedido_items`**: si el precio del plato cambia después, los pedidos y los cierres anteriores no se alteran.
- **Baja lógica de platos**: un plato retirado del menú sigue existiendo para los pedidos históricos.
- **Un cierre por fecha**: la restricción `UNIQUE` evita cerrar la caja dos veces el mismo día.
