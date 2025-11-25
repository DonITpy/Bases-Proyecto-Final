# Proyecto Bases - Sistema de Gestión de Flota Logística

## Descripción

Este proyecto es una aplicación web de gestión de flota logística construida con FastAPI (Python) y MySQL. Permite administrar vehículos, conductores, viajes, mantenimientos, consumos, incidencias, órdenes de servicio y usuarios. La aplicación utiliza sesiones para manejar autenticación y roles (admin, mecánico, usuario). Incluye una interfaz frontend basada en plantillas Jinja2 y funcionalidades para exportar datos en formato CSV.

El sistema está diseñado para facilitar el control y seguimiento de una flota de vehículos y sus operaciones logísticas.

---

## Tecnologías y Herramientas

- Python 3.11
- FastAPI
- MySQL 8.0
- Jinja2 (templating HTML)
- Docker y Docker Compose
- Uvicorn (servidor ASGI)
- ReportLab (generación de PDFs)
- Otros paquetes Python: mysql-connector-python, python-multipart, starlette, itsdangerous

---

## Estructura del Proyecto

```
Proyecto Bases/
├── backend/
│   ├── app.py               # Aplicación FastAPI con rutas y lógica backend
│   ├── Dockerfile           # Imagen Docker para la aplicación backend
│   ├── requirements.txt     # Dependencias Python
│   └── templates/           # Archivos HTML para la interfaz de usuario (Jinja2)
├── init/
│   └── scriptFlota.sql      # Script de inicialización y carga de datos en la base MySQL
├── docker-compose.yml       # Definición de servicios para levantar contenedores Docker (MySQL y backend)
```

---

## Configuración y Uso

### Requisitos previos

- Docker y Docker Compose instalados en el sistema.

### Levantar la aplicación con Docker Compose

Desde la raíz del proyecto, ejecutar:

```bash
docker-compose up --build
```

Esto levantará dos contenedores:

- **db**: servidor MySQL con la base `flota_logistica` y datos iniciales cargados desde `init/scriptFlota.sql`.
- **app**: aplicación FastAPI corriendo en `http://localhost:8000`.

### Acceso a la aplicación

Abrir en el navegador:  
`http://localhost:8000`

### Usuarios de ejemplo

- **Administrador**  
  - Correo: `admin@correo.com`  
  - Contraseña: `admin123`

- **Mecánico**  
  - Correo: `mecanico@correo.com`  
  - Contraseña: `mecanico123`

---

## Funcionalidades Principales

- Autenticación y manejo de sesiones con roles.
- Gestión CRUD para:
  - Vehículos
  - Conductores
  - Viajes
  - Mantenimientos
  - Consumos
  - Incidentes
  - Órdenes de servicio
  - Usuarios (solo admin)
- Exportación de reportes en CSV para vehículos, conductores, viajes y consumos.
- Rol de usuario "mecánico" limitado para mantenimiento, consumo e incidentes.
  
---

## Desarrollo

### Dependencias

Instalación manual (si no se usa Docker):

```bash
pip install -r backend/requirements.txt
```

### Ejecución local sin Docker

Ejecutar el servidor Uvicorn:

```bash
uvicorn backend.app:app --reload
```

Asegurarse de tener una base MySQL corriendo con la estructura y datos establecidos.

---

## Base de Datos

La base de datos utiliza codificación UTF-8 para soporte de acentos. Incluye tablas para usuarios, vehículos, conductores, viajes, mantenimientos, consumos, flotas, incidentes y órdenes de servicio con datos iniciales para pruebas.

Es configurada automáticamente por el contenedor MySQL mediante el script `init/scriptFlota.sql`.

---

## Licencia

Este proyecto es para uso educativo y de gestión interna.

---

## Contacto

Para consultas o soporte, contacta al desarrollador del proyecto.
