# Proyecto Bases - Sistema de Gestión de Flota Logística

## Descripción

Este proyecto es una aplicación web completa de gestión de flota logística construida con FastAPI (Python) y MySQL. Permite administrar de manera integral una flota de vehículos, incluyendo el seguimiento de conductores, viajes, mantenimientos, consumos de combustible, incidentes, órdenes de servicio, licencias, evaluaciones de desempeño y usuarios del sistema.

La aplicación implementa un sistema robusto de autenticación basado en sesiones con control de roles y permisos granulares. Incluye una interfaz web moderna basada en plantillas Jinja2, validaciones exhaustivas de datos, sistema de logs de auditoría, generación de reportes en CSV y PDF, y funcionalidades avanzadas de análisis de KPIs operativos.

El sistema está diseñado para facilitar el control operativo y estratégico de flotas vehiculares, optimizando costos, mejorando la seguridad y aumentando la eficiencia en las operaciones logísticas.

---

## Tecnologías y Herramientas

### Backend
- **Python 3.11**
- **FastAPI** - Framework web moderno y rápido para APIs REST
- **Uvicorn** - Servidor ASGI de alto rendimiento
- **MySQL 8.0** - Base de datos relacional con soporte UTF-8 completo
- **mysql-connector-python 8.0.33** - Conector oficial de MySQL para Python

### Frontend
- **Jinja2** - Motor de plantillas para renderizado HTML
- **Starlette** - Framework ASGI base de FastAPI
- **python-multipart** - Manejo de formularios multipart
- **itsdangerous** - Firma y verificación de datos

### Infraestructura
- **Docker & Docker Compose** - Contenedorización y orquestación
- **ReportLab** - Generación de documentos PDF

### Desarrollo
- **SessionMiddleware** - Manejo de sesiones de usuario
- **CSV/IO** - Exportación de datos
- **datetime** - Manejo de fechas y validaciones temporales

---

## Estructura del Proyecto

```
Proyecto Bases/
├── backend/
│   ├── app.py                    # Aplicación FastAPI principal con todas las rutas y lógica
│   ├── Dockerfile               # Imagen Docker para el backend
│   ├── requirements.txt         # Dependencias Python con versiones específicas
│   └── templates/               # Plantillas HTML Jinja2 para la interfaz web
│       ├── base.html           # Plantilla base con navegación y estilos
│       ├── login.html          # Página de autenticación
│       ├── home.html           # Dashboard principal
│       └── [otras plantillas]  # Páginas específicas por módulo
├── init/
│   └── scriptFlota.sql         # Script SQL completo de inicialización de BD

└── README.md                   # Esta documentación
```

---

## Base de Datos

### Esquema General

La base de datos `flota_logistica` utiliza codificación UTF-8 (`utf8mb4_unicode_ci`) para soporte completo de caracteres internacionales. El esquema está diseñado siguiendo principios de normalización y incluye las siguientes tablas principales:

### Tablas del Sistema

| Tabla | Descripción | Campos Principales |
|-------|-------------|-------------------|
| **usuario** | Usuarios del sistema con roles | id_usuario, nombre, correo, password, rol |
| **conductor** | Información de conductores | id_conductor, nombre, apellido, telefono, direccion, fecha_nacimiento, id_usuario |
| **licencia** | Licencias de conducir por conductor | id_licencia, id_conductor, tipo, fecha_emision, fecha_vencimiento |
| **evaluacion** | Evaluaciones de desempeño de conductores | id_evaluacion, id_conductor, fecha, puntuacion, comentarios |

### Tablas de Flota y Vehículos

| Tabla | Descripción | Campos Principales |
|-------|-------------|-------------------|
| **flota** | Grupos lógicos de vehículos | id_flota, nombre, descripcion, categoria, ubicacion, estado, capacidad_maxima |
| **vehiculo** | Información detallada de vehículos | id_vehiculo, matricula, modelo, tipo, capacidad, marca, estado, kilometraje, categoria |
| **flota_vehiculo** | Relación muchos-a-muchos flota-vehículo | id_flota, id_vehiculo |

### Tablas Operativas

| Tabla | Descripción | Campos Principales |
|-------|-------------|-------------------|
| **viaje** | Registros de viajes realizados | id_viaje, origen, destino, fecha_salida, fecha_estimada, estado, id_conductor, id_vehiculo |
| **orden_servicio** | Órdenes de trabajo/servicio | id_orden, descripcion, fecha, estado |
| **mantenimiento** | Registros de mantenimiento | id_mantenimiento, id_vehiculo, tipo, descripcion, costo, fecha |
| **consumo** | Registros de consumo de combustible | id_consumo, matricula, litros, fecha, tipo_combustible, costo |
| **incidente** | Incidentes y accidentes | id_incidente, matricula, tipo, fecha, descripcion |

### Tablas de Auditoría

| Tabla | Descripción | Campos Principales |
|-------|-------------|-------------------|
| **logs** | Registro de todas las operaciones | id_log, id_usuario, usuario_nombre, accion, tabla, registro_id, fecha_hora, detalle |

### Configuración Automática

La base de datos se inicializa automáticamente mediante el script `init/scriptFlota.sql` que incluye:
- Creación de todas las tablas con constraints
- Inserción de datos de prueba
- Configuración de índices para optimización
- Usuarios de ejemplo para testing

---

## Roles de Usuario y Permisos

El sistema implementa un control de acceso basado en roles con permisos granulares:

### **admin** (Administrador)
- Acceso completo a todas las funcionalidades
- Gestión de usuarios, conductores, vehículos y flotas
- Visualización de logs de auditoría
- Generación de reportes avanzados y KPIs
- Exportación de datos en CSV
- Configuración del sistema

### **conductor**
- Acceso limitado a sus propios datos y vehículos asignados
- Visualización de viajes, mantenimientos e incidentes relacionados
- Consulta de evaluaciones personales
- Acceso a licencias propias

### **mecanico** (Técnico/Mecánico)
- Gestión de mantenimientos y consumos
- Registro de incidentes
- Acceso limitado a vehículos para mantenimiento
- Generación de reportes de mantenimiento

### **logistica** (Operaciones Logísticas)
- Gestión completa de viajes y órdenes de servicio
- Asignación de conductores y vehículos
- Seguimiento de estado de operaciones
- Generación de reportes operativos

### **observador** (Solo Lectura)
- Acceso de lectura a la mayoría de módulos
- Sin permisos de modificación
- Ideal para supervisión y reporting

---

## API Endpoints

La aplicación expone una API RESTful completa. Los principales endpoints incluyen:

### Autenticación
- `GET /` - Redirección según estado de sesión
- `GET /login` - Página de login
- `POST /login` - Procesamiento de autenticación
- `GET /logout` - Cierre de sesión

### Dashboard
- `GET /home` - Dashboard principal

### Gestión de Vehículos
- `GET /vehiculos_web` - Lista de vehículos con filtros
- `POST /vehiculos_create` - Crear nuevo vehículo
- `GET /vehiculos_delete/{id}` - Eliminar vehículo
- `GET /vehiculos_edit/{id}` - Página de edición
- `POST /vehiculos_update/{id}` - Actualizar vehículo

### Gestión de Conductores
- `GET /conductores_web` - Lista de conductores
- `POST /conductores_create` - Crear conductor
- `GET /conductores_delete/{id}` - Eliminar conductor
- `GET /conductores_edit/{id}` - Página de edición
- `POST /conductores_update/{id}` - Actualizar conductor

### Gestión de Viajes
- `GET /viajes_web` - Lista de viajes con filtros
- `POST /viajes_create` - Crear viaje
- `GET /viajes_delete/{id}` - Eliminar viaje
- `GET /viajes_edit/{id}` - Página de edición
- `POST /viajes_update/{id}` - Actualizar viaje
- `GET /api/vehiculos_por_conductor/{id_conductor}` - API para vehículos por conductor

### Gestión de Mantenimiento
- `GET /mantenimiento_web` - Lista de mantenimientos
- `POST /mantenimiento_create` - Crear registro de mantenimiento
- `GET /mantenimiento_delete/{id}` - Eliminar mantenimiento
- `GET /mantenimiento_edit/{id}` - Página de edición
- `POST /mantenimiento_update/{id}` - Actualizar mantenimiento

### Gestión de Consumo
- `GET /consumo_web` - Lista de consumos
- `POST /consumo_create` - Crear registro de consumo
- `GET /consumo_delete/{id}` - Eliminar consumo
- `GET /consumo_edit/{id}` - Página de edición
- `POST /consumo_update/{id}` - Actualizar consumo

### Gestión de Incidentes
- `GET /incidentes_web` - Lista de incidentes
- `POST /incidentes_create` - Crear incidente
- `GET /incidentes_delete/{id}` - Eliminar incidente
- `GET /incidentes_edit/{id}` - Página de edición
- `POST /incidentes_update/{id}` - Actualizar incidente

### Gestión de Órdenes de Servicio
- `GET /ordenes_web` - Lista de órdenes
- `POST /ordenes_create` - Crear orden
- `GET /ordenes_delete/{id}` - Eliminar orden
- `GET /ordenes_edit/{id}` - Página de edición
- `POST /ordenes_update/{id}` - Actualizar orden

### Gestión de Flotas
- `GET /flota_web` - Lista de flotas
- `POST /flota_create` - Crear flota
- `GET /flota_delete/{id}` - Eliminar flota
- `GET /flota_edit/{id}` - Página de edición
- `POST /flota_update/{id}` - Actualizar flota

### Gestión de Licencias
- `GET /licencias_web` - Lista de licencias
- `POST /licencias_create` - Crear licencia
- `GET /licencias_delete/{id}` - Eliminar licencia
- `GET /licencias_edit/{id}` - Página de edición
- `POST /licencias_update/{id}` - Actualizar licencia

### Gestión de Evaluaciones
- `GET /evaluaciones_web` - Lista de evaluaciones
- `POST /evaluaciones_create` - Crear evaluación
- `GET /evaluaciones_delete/{id}` - Eliminar evaluación
- `GET /evaluaciones_edit/{id}` - Página de edición
- `POST /evaluaciones_update/{id}` - Actualizar evaluación

### Gestión de Usuarios
- `GET /usuarios_web` - Lista de usuarios (solo admin)
- `POST /usuarios_create` - Crear usuario (solo admin)
- `GET /usuarios_delete/{id}` - Eliminar usuario (solo admin)
- `GET /usuarios_edit/{id}` - Página de edición (solo admin)
- `POST /usuarios_update/{id}` - Actualizar usuario (solo admin)

### Logs y Auditoría
- `GET /logs_web` - Visualización de logs (solo admin)

### Reportes y Exportación
- `GET /reportes_web` - Dashboard de KPIs y reportes
- `GET /descargar_vehiculos_csv` - Exportar vehículos a CSV
- `GET /descargar_conductores_csv` - Exportar conductores a CSV
- `GET /descargar_viajes_csv` - Exportar viajes a CSV
- `GET /descargar_consumo_csv` - Exportar consumos a CSV
- `GET /descargar_reporte_general_csv` - Exportar reporte completo
- `GET /descargar_reporte_kpis_csv` - Exportar KPIs a CSV
- Varios endpoints específicos para reportes por conductor

---

## Configuración y Uso

### Requisitos previos

- Docker y Docker Compose instalados en el sistema
- Puerto 8000 disponible para la aplicación
- Puerto 3306 disponible para MySQL (o modificar docker-compose.yml)

### Levantar la aplicación con Docker Compose

Desde la raíz del proyecto, ejecutar:

```bash
docker-compose up --build
```

Esto levantará dos contenedores:

- **db**: Servidor MySQL 8.0 con la base `flota_logistica`
  - Puerto: `3306`
  - Usuario root: `root`
  - Password: `root`
  - Base de datos: `flota_logistica`
  - Codificación: `utf8mb4_unicode_ci`

- **app**: Aplicación FastAPI
  - Puerto: `8000`
  - Dependiente del contenedor `db`
  - Reinicio automático en caso de fallos

### Acceso a la aplicación

Abrir en el navegador: `http://localhost:8000`

### Usuarios de ejemplo

| Rol | Correo | Contraseña | Descripción |
|-----|--------|------------|-------------|
| **Administrador** | `admin@correo.com` | `admin123` | Acceso completo al sistema |
| **Mecánico** | `mecanico@correo.com` | `mecanico123` | Gestión de mantenimiento |
| **Conductor** | `conductor@correo.com` | `conductor123` | Acceso limitado a datos propios |

---

## Funcionalidades Principales

### Gestión Integral de Flota
- **CRUD completo** para vehículos, conductores, viajes y flotas
- **Asignación dinámica** de conductores a vehículos y viajes
- **Seguimiento de estado** de vehículos (activo, inactivo, mantenimiento)
- **Categorización** de vehículos y flotas por tipo y capacidad

### Operaciones Logísticas
- **Planificación y seguimiento** de viajes con fechas estimadas
- **Gestión de órdenes de servicio** con estados operativos
- **Control de consumos** de combustible con tipos y costos
- **Registro de incidentes** clasificados por tipo

### Mantenimiento y Seguridad
- **Programación de mantenimientos** preventivo y correctivo
- **Evaluaciones de desempeño** de conductores (1-10 puntos)
- **Control de licencias** con alertas de vencimiento
- **Sistema de logs** completo para auditoría

### Reportes y Analytics
- **KPIs operativos** en tiempo real (cumplimiento, costos, incidentes)
- **Exportación CSV** de todos los módulos
- **Reportes cruzados** (costos operativos, desempeño por conductor)
- **Dashboard ejecutivo** con métricas clave

### Seguridad y Validaciones
- **Autenticación robusta** con sesiones seguras
- **Control de permisos** granular por rol
- **Validaciones exhaustivas** en todos los formularios
- **Prevención de inyección SQL** mediante prepared statements
- **Logs de auditoría** de todas las operaciones

---

## Desarrollo

### Instalación manual (sin Docker)

1. **Instalar dependencias Python:**
```bash
pip install -r backend/requirements.txt
```

2. **Configurar base de datos MySQL:**
   - Crear base de datos `flota_logistica`
   - Ejecutar el script `init/scriptFlota.sql`
   - Configurar usuario con permisos adecuados

3. **Ejecutar la aplicación:**
```bash
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

### Variables de entorno

La aplicación puede configurarse mediante variables de entorno:
- `MYSQL_HOST`: Host del servidor MySQL (default: `db` en Docker)
- `MYSQL_USER`: Usuario MySQL (default: `root`)
- `MYSQL_PASSWORD`: Password MySQL (default: `root`)
- `MYSQL_DATABASE`: Nombre de la base de datos (default: `flota_logistica`)

### Estructura de la aplicación

El archivo `backend/app.py` contiene:
- **Configuración FastAPI** con middleware de sesiones
- **Conexión a BD** con reintentos automáticos
- **Funciones helper** para logging y validaciones
- **Rutas organizadas** por módulos (vehículos, conductores, etc.)
- **Validaciones de negocio** en cada endpoint
- **Gestión de errores** y redirecciones apropiadas

---

## Logs y Auditoría

El sistema incluye un completo sistema de auditoría que registra todas las operaciones:

- **Tabla logs**: Almacena fecha, usuario, acción, tabla afectada y detalles
- **Acciones auditadas**: crear, modificar, eliminar
- **Interfaz de consulta**: Filtros por usuario, tabla, acción y fecha
- **Propósito**: Cumplimiento normativo y troubleshooting

---

## Licencia

Este proyecto es desarrollado con fines educativos y de gestión interna. No incluye licencia específica - consultar con el desarrollador para usos comerciales.

---

## Contacto

Para consultas técnicas, soporte o colaboraciones, contactar al equipo de desarrollo del proyecto.
