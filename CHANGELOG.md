# Historial de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y [versionado semántico](https://semver.org/lang/es/).

## [Sin publicar]

### Cambiado
- README orientado a la entrega del taller: identificación de la línea base, pasos para verificarla, criterios de aprobación, historial incluido, flujo de control de cambios y endpoints de la API.

## [1.0.0] – 2026-11-10 · Línea base del código fuente

Primera versión estable del SIGR. A partir de aquí, cualquier cambio necesita una solicitud de cambio (issue), una rama propia y un pull request aprobado.

### Agregado
- Autenticación: registro público de clientes, creación de personal por el administrador, login con token firmado (8 horas) y permisos por rol.
- Menú digital: CRUD de categorías y platos. Los platos se dan de baja de forma lógica y una categoría solo se elimina si no tiene platos.
- Pedidos: registro por mesa con cálculo del total y seguimiento por estados (recibido → en preparación → listo → entregado → pagado, o cancelado).
- Reservas: por fecha y hora, sin cruces de más de dos horas en la misma mesa, y cancelación.
- Caja: reporte de ventas del día por plato y cierre de caja único por fecha.
- Esquema de base de datos SQLite (`db/schema.sql`).
- 10 pruebas básicas de integración de los cinco módulos (`tests/`).
- Documentación: README, estructura de base de datos y manual de despliegue.
- Licencia MIT.

### Corregido
- La validación de platos ya no acepta valores booleanos como precio.

### Pendiente para la siguiente versión
- Ajustar al límite de 79 caracteres de PEP 8 las líneas largas (consultas SQL y pruebas) y verificarlo con flake8 en el pipeline.
