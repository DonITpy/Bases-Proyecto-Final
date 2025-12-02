from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import mysql.connector
import time
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import csv
import io
from datetime import datetime

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecret")

# Motor de plantillas Jinja2; todas las páginas extienden de base.html para consistencia visual
templates = Jinja2Templates(directory="templates")

def get_db():
    """Obtiene una conexión resiliente a MySQL con reintentos.
    Importante para ambientes con Docker donde el contenedor puede tardar en estar listo.
    """
    for _ in range(10):
        try:
            conn = mysql.connector.connect(
                host='db',
                user='root',
                password='root',
                database='flota_logistica',
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                use_unicode=True
            )
            return conn
        except:
            time.sleep(2)
    return None

# --- HELPER: REGISTRAR LOG ---
def registrar_log(id_usuario, usuario_nombre, accion, tabla, registro_id=None, detalle=""):
    """
    Registra una operación en la tabla de logs.
    accion: 'crear', 'modificar', 'eliminar'
    tabla: nombre de la tabla afectada
    registro_id: ID del registro afectado
    detalle: información adicional sobre la operación
    """
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO logs (id_usuario, usuario_nombre, accion, tabla, registro_id, detalle)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (id_usuario, usuario_nombre, accion, tabla, registro_id, detalle))
        db.commit()
        db.close()
    except Exception as e:
        print(f"Error al registrar log: {e}")

# --- REDIRECCIONAMIENTO ---
@app.get("/")
def root(request: Request):
    usuario = request.session.get("usuario")
    if usuario:
        return RedirectResponse("/home", status_code=303)
    else:
        return RedirectResponse("/login", status_code=303)

# --- LOGIN -----
@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})

@app.post("/login")
def login_post(request: Request, correo: str = Form(...), password: str = Form(...)):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.*, c.id_conductor
        FROM usuario u
        LEFT JOIN conductor c ON c.id_usuario = u.id_usuario
        WHERE u.correo=%s AND u.password=%s
    """, (correo, password))
    usuario = cursor.fetchone()
    db.close()
    if usuario:
        request.session["usuario"] = usuario
        return RedirectResponse("/home", status_code=303)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Usuario o contraseña inválidos"})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)

# --- HOME ----
@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("home.html", {"request": request, "usuario": usuario})

# ==================== LOGS ====================
@app.get("/logs_web")
def logs_web(request: Request, buscar: str = "", filtro_tabla: str = "", filtro_accion: str = ""):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/home", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM logs WHERE 1=1"
    params = []
    
    if buscar:
        query += " AND (usuario_nombre LIKE %s OR detalle LIKE %s OR tabla LIKE %s)"
        search_param = f"%{buscar}%"
        params.extend([search_param, search_param, search_param])
    
    if filtro_tabla:
        query += " AND tabla = %s"
        params.append(filtro_tabla)
    
    if filtro_accion:
        query += " AND accion = %s"
        params.append(filtro_accion)
    
    query += " ORDER BY fecha_hora DESC LIMIT 1000"
    
    cursor.execute(query, params)
    logs = cursor.fetchall()
    
    # Obtener listas únicas de tablas para filtros
    cursor.execute("SELECT DISTINCT tabla FROM logs ORDER BY tabla")
    tablas = cursor.fetchall()
    
    db.close()
    
    return templates.TemplateResponse("logs.html", {
        "request": request,
        "logs": logs,
        "usuario": usuario,
        "buscar": buscar,
        "filtro_tabla": filtro_tabla,
        "filtro_accion": filtro_accion,
        "tablas": tablas
    })

# ==================== VEHICULOS ====================
@app.get("/vehiculos_web")
def vehiculos_web(request: Request, buscar: str = "", filtro_estado: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    if usuario.get("rol") == "conductor" and usuario.get("id_conductor"):
        query = """
            SELECT * FROM vehiculo WHERE id_vehiculo IN (
                SELECT DISTINCT id_vehiculo FROM viaje WHERE id_conductor = %s AND id_vehiculo IS NOT NULL
            )
        """
        params = [usuario.get("id_conductor")]
        if buscar:
            query = "SELECT * FROM (" + query + ") t WHERE (matricula LIKE %s OR modelo LIKE %s OR marca LIKE %s)"
            params = params + [f"%{buscar}%", f"%{buscar}%", f"%{buscar}%"]
        if filtro_estado:
            query = "SELECT * FROM (" + query + ") t WHERE estado = %s" if not buscar else query + " AND estado = %s"
            params.append(filtro_estado)
    else:
        query = "SELECT * FROM vehiculo WHERE 1=1"
        params = []
        if buscar:
            query += " AND (matricula LIKE %s OR modelo LIKE %s OR marca LIKE %s)"
            params.extend([f"%{buscar}%", f"%{buscar}%", f"%{buscar}%"])
        if filtro_estado:
            query += " AND estado = %s"
            params.append(filtro_estado)
    
    cursor.execute(query, params)
    vehiculos = cursor.fetchall()
    db.close()
    
    return templates.TemplateResponse("vehiculos.html", {
        "request": request, 
        "vehiculos": vehiculos, 
        "usuario": usuario,
        "buscar": buscar,
        "filtro_estado": filtro_estado
    })

@app.post("/vehiculos_create")
def vehiculos_create(request: Request, matricula: str = Form(...), modelo: str = Form(...), tipo: str = Form(...), capacidad: int = Form(...), marca: str = Form(...), estado: str = Form(...), kilometraje: int = Form(...), categoria: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] not in ["admin"]:
        return RedirectResponse("/vehiculos_web", status_code=303)
    
    # VALIDACIONES
    error_msg = None
    
    # Validar matrícula
    if not matricula or len(matricula) < 3 or len(matricula) > 20:
        error_msg = "La matrícula debe tener entre 3 y 20 caracteres"
    elif not matricula.isalnum() or not matricula.isupper():
        error_msg = "La matrícula debe contener solo mayúsculas y números"
    
    # Validar modelo
    elif not modelo or len(modelo) < 1 or len(modelo) > 50:
        error_msg = "El modelo debe tener entre 1 y 50 caracteres"
    elif not all(c.isalnum() or c.isspace() or c == '-' for c in modelo):
        error_msg = "El modelo contiene caracteres inválidos"
    
    # Validar tipo
    elif not tipo or len(tipo) < 1 or len(tipo) > 30:
        error_msg = "El tipo debe tener entre 1 y 30 caracteres"
    elif not all(c.isalpha() or c.isspace() or c == '-' for c in tipo):
        error_msg = "El tipo debe contener solo letras, espacios y guiones"
    
    # Validar capacidad
    elif capacidad < 1 or capacidad > 100000:
        error_msg = "La capacidad debe estar entre 1 y 100,000"
    
    # Validar marca
    elif not marca or len(marca) < 1 or len(marca) > 30:
        error_msg = "La marca debe tener entre 1 y 30 caracteres"
    elif not all(c.isalpha() or c.isspace() or c == '-' for c in marca):
        error_msg = "La marca debe contener solo letras, espacios y guiones"
    
    # Validar estado
    elif estado not in ['activo', 'inactivo', 'mantenimiento']:
        error_msg = "El estado no es válido"
    
    # Validar kilometraje
    elif kilometraje < 0 or kilometraje > 9999999:
        error_msg = "El kilometraje debe estar entre 0 y 9,999,999"
    
    # Validar categoría
    elif categoria not in ['carga_ligera','carga_pesada','transporte_personal','reparto','especial']:
        error_msg = "La categoría no es válida"
    
    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vehiculo")
        vehiculos = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("vehiculos.html", {
            "request": request, 
            "vehiculos": vehiculos, 
            "usuario": usuario,
            "error": error_msg
        })
    
    db = get_db()
    cursor = db.cursor()
    
    # Validar que la matrícula no exista
    cursor.execute("SELECT * FROM vehiculo WHERE matricula=%s", (matricula,))
    if cursor.fetchone():
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM vehiculo")
        vehiculos = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("vehiculos.html", {
            "request": request, 
            "vehiculos": vehiculos, 
            "usuario": usuario,
            "error": "La matrícula ya existe en el sistema"
        })
    
    try:
        cursor.execute(
            "INSERT INTO vehiculo (matricula, modelo, tipo, capacidad, marca, estado, kilometraje, categoria) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (matricula, modelo, tipo, capacidad, marca, estado, kilometraje, categoria)
        )
        vehiculo_id = cursor.lastrowid
        db.commit()
        db.close()
        
        # Registrar log
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "crear",
            "vehiculo",
            vehiculo_id,
            f"Vehículo {matricula} - {marca} {modelo}"
        )
        
        return RedirectResponse("/vehiculos_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM vehiculo")
        vehiculos = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("vehiculos.html", {
            "request": request, 
            "vehiculos": vehiculos, 
            "usuario": usuario,
            "error": f"Error al crear vehículo: {str(e)}"
        })

@app.get("/vehiculos_delete/{id}")
def vehiculos_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/vehiculos_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener datos del vehículo antes de eliminar
    cursor.execute("SELECT matricula, marca, modelo FROM vehiculo WHERE id_vehiculo=%s", (id,))
    vehiculo = cursor.fetchone()
    
    try:
        cursor.execute("DELETE FROM vehiculo WHERE id_vehiculo=%s", (id,))
        db.commit()
        db.close()
        
        # Registrar log
        if vehiculo:
            registrar_log(
                usuario["id_usuario"],
                usuario["nombre"],
                "eliminar",
                "vehiculo",
                id,
                f"Vehículo {vehiculo['matricula']} - {vehiculo['marca']} {vehiculo['modelo']}"
            )
        
        return RedirectResponse("/vehiculos_web", status_code=303)
    except Exception as e:
        db.close()
        # Retorna a la página con mensaje de error
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM vehiculo")
        vehiculos = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("vehiculos.html", {
            "request": request, 
            "vehiculos": vehiculos, 
            "usuario": usuario,
            "error": "No se puede eliminar este vehículo porque tiene registros vinculados (mantenimiento, consumo, incidentes, viajes, etc). Elimina primero esos registros."
        })

@app.get("/vehiculos_edit/{id}")
def vehiculos_edit(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] not in ["admin", "mecanico", "logistica"]:
        return RedirectResponse("/vehiculos_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM vehiculo WHERE id_vehiculo=%s", (id,))
    vehiculo = cursor.fetchone()
    db.close()
    
    if not vehiculo:
        return RedirectResponse("/vehiculos_web", status_code=303)
    
    return templates.TemplateResponse("vehiculos_edit.html", {"request": request, "vehiculo": vehiculo, "usuario": usuario})

@app.post("/vehiculos_update/{id}")
def vehiculos_update(request: Request, id: int, matricula: str = Form(...), modelo: str = Form(...), tipo: str = Form(...), capacidad: int = Form(...), marca: str = Form(...), estado: str = Form(...), kilometraje: int = Form(...), categoria: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] not in ["admin", "mecanico", "logistica"]:
        return RedirectResponse("/vehiculos_web", status_code=303)
    
    # VALIDACIONES
    error_msg = None
    
    # Validar matrícula
    if not matricula or len(matricula) < 3 or len(matricula) > 20:
        error_msg = "La matrícula debe tener entre 3 y 20 caracteres"
    elif not matricula.isalnum() or not matricula.isupper():
        error_msg = "La matrícula debe contener solo mayúsculas y números"
    
    # Validar modelo
    elif not modelo or len(modelo) < 1 or len(modelo) > 50:
        error_msg = "El modelo debe tener entre 1 y 50 caracteres"
    elif not all(c.isalnum() or c.isspace() or c == '-' for c in modelo):
        error_msg = "El modelo contiene caracteres inválidos"
    
    # Validar tipo
    elif not tipo or len(tipo) < 1 or len(tipo) > 30:
        error_msg = "El tipo debe tener entre 1 y 30 caracteres"
    elif not all(c.isalpha() or c.isspace() or c == '-' for c in tipo):
        error_msg = "El tipo debe contener solo letras, espacios y guiones"
    
    # Validar capacidad
    elif capacidad < 1 or capacidad > 100000:
        error_msg = "La capacidad debe estar entre 1 y 100,000"
    
    # Validar marca
    elif not marca or len(marca) < 1 or len(marca) > 30:
        error_msg = "La marca debe tener entre 1 y 30 caracteres"
    elif not all(c.isalpha() or c.isspace() or c == '-' for c in marca):
        error_msg = "La marca debe contener solo letras, espacios y guiones"
    
    # Validar estado
    elif estado not in ['activo', 'inactivo', 'mantenimiento']:
        error_msg = "El estado no es válido"
    
    # Validar kilometraje
    elif kilometraje < 0 or kilometraje > 9999999:
        error_msg = "El kilometraje debe estar entre 0 y 9,999,999"
    
    # Validar categoría
    elif categoria not in ['carga_ligera','carga_pesada','transporte_personal','reparto','especial']:
        error_msg = "La categoría no es válida"
    
    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vehiculo WHERE id_vehiculo=%s", (id,))
        vehiculo = cursor.fetchone()
        db.close()
        return templates.TemplateResponse("vehiculos_edit.html", {
            "request": request,
            "vehiculo": vehiculo,
            "usuario": usuario,
            "error": error_msg
        })
    
    db = get_db()
    cursor = db.cursor()
    
    # Validar que la matrícula no exista (excepto la del vehículo actual)
    cursor.execute("SELECT * FROM vehiculo WHERE matricula=%s AND id_vehiculo!=%s", (matricula, id))
    if cursor.fetchone():
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM vehiculo WHERE id_vehiculo=%s", (id,))
        vehiculo = cursor2.fetchone()
        db2.close()
        return templates.TemplateResponse("vehiculos_edit.html", {
            "request": request,
            "vehiculo": vehiculo,
            "usuario": usuario,
            "error": "La matrícula ya existe en otro vehículo"
        })
    
    try:
        cursor.execute(
            "UPDATE vehiculo SET matricula=%s, modelo=%s, tipo=%s, capacidad=%s, marca=%s, estado=%s, kilometraje=%s, categoria=%s WHERE id_vehiculo=%s",
            (matricula, modelo, tipo, capacidad, marca, estado, kilometraje, categoria, id)
        )
        db.commit()
        db.close()
        
        # Registrar log
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "modificar",
            "vehiculo",
            id,
            f"Vehículo {matricula} - {marca} {modelo}"
        )
        
        return RedirectResponse("/vehiculos_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM vehiculo WHERE id_vehiculo=%s", (id,))
        vehiculo = cursor2.fetchone()
        db2.close()
        return templates.TemplateResponse("vehiculos_edit.html", {
            "request": request,
            "vehiculo": vehiculo,
            "usuario": usuario,
            "error": f"Error al actualizar: {str(e)}"
        })
  
# ==================== CONDUCTORES ====================
@app.get("/conductores_web")
def conductores_web(request: Request, buscar: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM conductor WHERE 1=1"
    params = []
    
    # Si es conductor, solo ve sus propios datos
    if usuario.get("rol") == "conductor":
        id_conductor = usuario.get("id_conductor")
        if id_conductor:
            query += " AND id_conductor = %s"
            params.append(id_conductor)
        else:
            # Si es conductor pero no tiene id_conductor, no ve nada
            cursor.execute("SELECT * FROM conductor WHERE 1=0")
            conductores = cursor.fetchall()
            db.close()
            return templates.TemplateResponse("conductores.html", {
                "request": request, 
                "conductores": conductores, 
                "usuario": usuario,
                "buscar": buscar
            })
    
    # Búsqueda por nombre o apellido (solo para admin)
    if buscar and usuario.get("rol") == "admin":
        query += " AND (nombre LIKE %s OR apellido LIKE %s)"
        params.extend([f"%{buscar}%", f"%{buscar}%"])
    
    cursor.execute(query, params)
    conductores = cursor.fetchall()
    db.close()
    
    return templates.TemplateResponse("conductores.html", {
        "request": request, 
        "conductores": conductores, 
        "usuario": usuario,
        "buscar": buscar
    })

@app.post("/conductores_create")
def conductores_create(request: Request, nombre: str = Form(...), apellido: str = Form(...), telefono: str = Form(...), direccion: str = Form(...), fecha_nacimiento: str = Form(...), id_usuario: int = Form(None)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO conductor (nombre, apellido, telefono, direccion, fecha_nacimiento, id_usuario) VALUES (%s,%s,%s,%s,%s,%s)",
                   (nombre, apellido, telefono, direccion, fecha_nacimiento, id_usuario))
    conductor_id = cursor.lastrowid
    db.commit()
    db.close()
    
    # Registrar log
    registrar_log(
        usuario["id_usuario"],
        usuario["nombre"],
        "crear",
        "conductor",
        conductor_id,
        f"Conductor {nombre} {apellido}"
    )
    
    return RedirectResponse("/conductores_web", status_code=303)
    
    # VALIDACIONES
    error_msg = None
    
    # Validar nombre
    if not nombre or len(nombre) < 2 or len(nombre) > 60:
        error_msg = "El nombre debe tener entre 2 y 60 caracteres"
    elif not all(c.isalpha() or c.isspace() or c == '-' for c in nombre):
        error_msg = "El nombre solo debe contener letras, espacios y guiones"
    
    # Validar apellido
    elif not apellido or len(apellido) < 2 or len(apellido) > 60:
        error_msg = "El apellido debe tener entre 2 y 60 caracteres"
    elif not all(c.isalpha() or c.isspace() or c == '-' for c in apellido):
        error_msg = "El apellido solo debe contener letras, espacios y guiones"
    
    # Validar teléfono
    elif not telefono or len(telefono) < 7 or len(telefono) > 20:
        error_msg = "El teléfono debe tener entre 7 y 20 caracteres"
    elif not all(c.isdigit() or c in ['-', '+', ' ', '(', ')'] for c in telefono):
        error_msg = "El teléfono contiene caracteres inválidos"
    
    # Validar dirección
    elif not direccion or len(direccion) < 5 or len(direccion) > 100:
        error_msg = "La dirección debe tener entre 5 y 100 caracteres"
    
    # Validar fecha de nacimiento
    elif not fecha_nacimiento:
        error_msg = "La fecha de nacimiento es obligatoria"
    else:
        try:
            from datetime import datetime
            fecha_obj = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
            edad = (datetime.now() - fecha_obj).days // 365
            if edad < 18:
                error_msg = "El conductor debe ser mayor de 18 años"
            elif edad > 120:
                error_msg = "La fecha de nacimiento no es válida"
        except:
            error_msg = "Formato de fecha inválido (use YYYY-MM-DD)"
    
    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM conductor")
        conductores = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("conductores.html", {
            "request": request, 
            "conductores": conductores, 
            "usuario": usuario,
            "error": error_msg
        })
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO conductor (nombre, apellido, telefono, direccion, fecha_nacimiento) VALUES (%s,%s,%s,%s,%s)",
                       (nombre, apellido, telefono, direccion, fecha_nacimiento))
        db.commit()
        db.close()
        return RedirectResponse("/conductores_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM conductor")
        conductores = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("conductores.html", {
            "request": request, 
            "conductores": conductores, 
            "usuario": usuario,
            "error": f"Error al crear conductor: {str(e)}"
        })

@app.get("/conductores_delete/{id}")
def conductores_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/conductores_web", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener datos antes de eliminar
    cursor.execute("SELECT nombre, apellido FROM conductor WHERE id_conductor=%s", (id,))
    conductor = cursor.fetchone()
    
    cursor.execute("DELETE FROM conductor WHERE id_conductor=%s", (id,))
    db.commit()
    db.close()
    
    # Registrar log
    if conductor:
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "eliminar",
            "conductor",
            id,
            f"Conductor {conductor['nombre']} {conductor['apellido']}"
        )
    
    return RedirectResponse("/conductores_web", status_code=303)

@app.get("/conductores_edit/{id}")
def conductores_edit(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/conductores_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM conductor WHERE id_conductor=%s", (id,))
    conductor = cursor.fetchone()
    db.close()
    
    if not conductor:
        return RedirectResponse("/conductores_web", status_code=303)
    
    return templates.TemplateResponse("conductores_edit.html", {"request": request, "conductor": conductor, "usuario": usuario})

@app.post("/conductores_update/{id}")
def conductores_update(request: Request, id: int, nombre: str = Form(...), apellido: str = Form(...), telefono: str = Form(...), direccion: str = Form(...), fecha_nacimiento: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/conductores_web", status_code=303)
    
    # VALIDACIONES (mismo patrón que create)
    error_msg = None
    
    # Validar nombre
    if not nombre or len(nombre) < 2 or len(nombre) > 60:
        error_msg = "El nombre debe tener entre 2 y 60 caracteres"
    elif not all(c.isalpha() or c.isspace() or c == '-' for c in nombre):
        error_msg = "El nombre solo debe contener letras, espacios y guiones"
    
    # Validar apellido
    elif not apellido or len(apellido) < 2 or len(apellido) > 60:
        error_msg = "El apellido debe tener entre 2 y 60 caracteres"
    elif not all(c.isalpha() or c.isspace() or c == '-' for c in apellido):
        error_msg = "El apellido solo debe contener letras, espacios y guiones"
    
    # Validar teléfono
    elif not telefono or len(telefono) < 7 or len(telefono) > 20:
        error_msg = "El teléfono debe tener entre 7 y 20 caracteres"
    elif not all(c.isdigit() or c in ['-', '+', ' ', '(', ')'] for c in telefono):
        error_msg = "El teléfono contiene caracteres inválidos"
    
    # Validar dirección
    elif not direccion or len(direccion) < 5 or len(direccion) > 100:
        error_msg = "La dirección debe tener entre 5 y 100 caracteres"
    
    # Validar fecha de nacimiento
    elif not fecha_nacimiento:
        error_msg = "La fecha de nacimiento es obligatoria"
    else:
        try:
            from datetime import datetime
            fecha_obj = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
            edad = (datetime.now() - fecha_obj).days // 365
            if edad < 18:
                error_msg = "El conductor debe ser mayor de 18 años"
            elif edad > 120:
                error_msg = "La fecha de nacimiento no es válida"
        except:
            error_msg = "Formato de fecha inválido (use YYYY-MM-DD)"
    
    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM conductor WHERE id_conductor=%s", (id,))
        conductor = cursor.fetchone()
        db.close()
        return templates.TemplateResponse("conductores_edit.html", {
            "request": request,
            "conductor": conductor,
            "usuario": usuario,
            "error": error_msg
        })
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE conductor SET nombre=%s, apellido=%s, telefono=%s, direccion=%s, fecha_nacimiento=%s WHERE id_conductor=%s",
            (nombre, apellido, telefono, direccion, fecha_nacimiento, id)
        )
        db.commit()
        db.close()
        
        # Registrar log
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "modificar",
            "conductor",
            id,
            f"Conductor {nombre} {apellido}"
        )
        
        return RedirectResponse("/conductores_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM conductor WHERE id_conductor=%s", (id,))
        conductor = cursor2.fetchone()
        db2.close()
        return templates.TemplateResponse("conductores_edit.html", {
            "request": request,
            "conductor": conductor,
            "usuario": usuario,
            "error": "Error al actualizar conductor"
        })

# ==================== VIAJES ====================
@app.get("/viajes_web")
def viajes_web(request: Request, buscar: str = "", filtro_estado: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # seleccionar viajes junto con nombre del conductor
    base_query = """
        SELECT v.*, c.nombre AS nombre_conductor, c.apellido AS apellido_conductor
        FROM viaje v
        LEFT JOIN conductor c ON v.id_conductor = c.id_conductor
        WHERE 1=1
    """
    params = []

    if usuario.get("rol") == "conductor" and usuario.get("id_conductor"):
        base_query += " AND v.id_conductor = %s"
        params.append(usuario.get("id_conductor"))

    if buscar:
        base_query += " AND (v.origen LIKE %s OR v.destino LIKE %s)"
        params.extend([f"%{buscar}%", f"%{buscar}%"])
    if filtro_estado:
        base_query += " AND v.estado = %s"
        params.append(filtro_estado)

    base_query += " ORDER BY v.fecha_salida DESC, v.id_viaje DESC"
    cursor.execute(base_query, params)
    viajes = cursor.fetchall()

    # lista de conductores para el select (creación/edición)
    cursor.execute("SELECT id_conductor, nombre, apellido FROM conductor ORDER BY nombre, apellido")
    conductores_list = cursor.fetchall()
    
    # lista de vehículos para el select
    cursor.execute("SELECT id_vehiculo, matricula, modelo, id_conductor FROM vehiculo ORDER BY matricula")
    vehiculos_list = cursor.fetchall()

    db.close()

    return templates.TemplateResponse("viajes.html", {
        "request": request,
        "viajes": viajes,
        "usuario": usuario,
        "buscar": buscar,
        "filtro_estado": filtro_estado,
        "conductores_list": conductores_list,
        "vehiculos_list": vehiculos_list
    })

@app.post("/viajes_create")
def viajes_create(request: Request, origen: str = Form(...), destino: str = Form(...),
                  fecha_salida: str = Form(...), fecha_estimada: str = Form(None),
                  estado: str = Form(...), id_conductor: int = Form(None), id_vehiculo: int = Form(None)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] not in ["admin", "logistica"]:
        return RedirectResponse("/viajes_web", status_code=303)

    # VALIDACIONES
    error_msg = None

    if not origen or not destino:
        error_msg = "Origen y destino obligatorios"

    if not error_msg:
        try:
            fecha_obj = datetime.strptime(fecha_salida, "%Y-%m-%d")
        except:
            error_msg = "Fecha de salida inválida (use YYYY-MM-DD)"

    if not error_msg and fecha_estimada:
        try:
            fecha_est_obj = datetime.strptime(fecha_estimada, "%Y-%m-%d")
            fecha_salida_obj = datetime.strptime(fecha_salida, "%Y-%m-%d")
            if fecha_est_obj.date() < fecha_salida_obj.date():
                error_msg = "La fecha estimada no puede ser anterior a la fecha de salida"
        except:
            error_msg = "Fecha estimada inválida (use YYYY-MM-DD)"

    if not error_msg:
        if estado not in ['pendiente', 'en progreso', 'completado', 'cancelado']:
            error_msg = "Estado no válido"

    # validar conductor si se envía
    if not error_msg and id_conductor:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id_conductor FROM conductor WHERE id_conductor=%s", (id_conductor,))
        if not cursor.fetchone():
            db.close()
            error_msg = "Conductor seleccionado no existe"
        else:
            db.close()
    
    # validar vehículo si se envía
    if not error_msg and id_vehiculo:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id_vehiculo FROM vehiculo WHERE id_vehiculo=%s", (id_vehiculo,))
        if not cursor.fetchone():
            db.close()
            error_msg = "Vehículo seleccionado no existe"
        else:
            db.close()

    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT v.*, c.nombre AS nombre_conductor, c.apellido AS apellido_conductor
            FROM viaje v
            LEFT JOIN conductor c ON v.id_conductor = c.id_conductor
        """)
        viajes = cursor.fetchall()
        cursor.execute("SELECT id_conductor, nombre, apellido FROM conductor ORDER BY nombre, apellido")
        conductores_list = cursor.fetchall()
        cursor.execute("SELECT id_vehiculo, matricula, modelo, id_conductor FROM vehiculo ORDER BY matricula")
        vehiculos_list = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("viajes.html", {
            "request": request,
            "viajes": viajes,
            "usuario": usuario,
            "error": error_msg,
            "conductores_list": conductores_list,
            "vehiculos_list": vehiculos_list,
            "buscar": "",
            "filtro_estado": ""
        })

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO viaje (origen, destino, fecha_salida, fecha_estimada, estado, id_conductor, id_vehiculo) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (origen, destino, fecha_salida, fecha_estimada if fecha_estimada else None, estado, id_conductor if id_conductor else None, id_vehiculo if id_vehiculo else None)
        )
        viaje_id = cursor.lastrowid
        db.commit()
        db.close()
        
        # Registrar log
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "crear",
            "viaje",
            viaje_id,
            f"Viaje {origen} → {destino}"
        )
        
        return RedirectResponse("/viajes_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("""
            SELECT v.*, c.nombre AS nombre_conductor, c.apellido AS apellido_conductor
            FROM viaje v
            LEFT JOIN conductor c ON v.id_conductor = c.id_conductor
        """)
        viajes = cursor2.fetchall()
        cursor2.execute("SELECT id_conductor, nombre, apellido FROM conductor ORDER BY nombre, apellido")
        conductores_list = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("viajes.html", {
            "request": request,
            "viajes": viajes,
            "usuario": usuario,
            "error": f"Error al crear viaje: {str(e)}",
            "conductores_list": conductores_list,
            "buscar": "",
            "filtro_estado": ""
        })

@app.get("/viajes_delete/{id}")
def viajes_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/viajes_web", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener datos antes de eliminar
    cursor.execute("SELECT origen, destino FROM viaje WHERE id_viaje=%s", (id,))
    viaje = cursor.fetchone()
    
    cursor.execute("DELETE FROM viaje WHERE id_viaje=%s", (id,))
    db.commit()
    db.close()
    
    # Registrar log
    if viaje:
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "eliminar",
            "viaje",
            id,
            f"Viaje {viaje['origen']} → {viaje['destino']}"
        )
    
    return RedirectResponse("/viajes_web", status_code=303)

@app.get("/api/vehiculos_por_conductor/{id_conductor}")
def get_vehiculos_por_conductor(request: Request, id_conductor: int):
    """API endpoint para obtener vehículos de un conductor específico"""
    from fastapi.responses import JSONResponse
    
    usuario = request.session.get("usuario")
    if not usuario:
        return JSONResponse({"error": "No autorizado"}, status_code=401)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT id_vehiculo, matricula, modelo, marca FROM vehiculo WHERE id_conductor = %s ORDER BY matricula",
        (id_conductor,)
    )
    vehiculos = cursor.fetchall()
    db.close()
    
    return JSONResponse(vehiculos)

@app.get("/viajes_edit/{id}")
def viajes_edit(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] not in ["admin", "logistica"]:
        return RedirectResponse("/viajes_web", status_code=303)

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM viaje WHERE id_viaje=%s", (id,))
    viaje = cursor.fetchone()
    cursor.execute("SELECT id_conductor, nombre, apellido FROM conductor ORDER BY nombre, apellido")
    conductores_list = cursor.fetchall()
    cursor.execute("SELECT id_vehiculo, matricula, modelo, id_conductor FROM vehiculo ORDER BY matricula")
    vehiculos_list = cursor.fetchall()
    db.close()

    if not viaje:
        return RedirectResponse("/viajes_web", status_code=303)

    return templates.TemplateResponse("viajes_edit.html", {
        "request": request, 
        "viaje": viaje, 
        "usuario": usuario, 
        "conductores_list": conductores_list,
        "vehiculos_list": vehiculos_list
    })

@app.post("/viajes_update/{id}")
def viajes_update(request: Request, id: int, origen: str = Form(...), destino: str = Form(...),
                  fecha_salida: str = Form(...), fecha_estimada: str = Form(None), estado: str = Form(...), id_conductor: int = Form(None)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] not in ["admin", "logistica"]:
        return RedirectResponse("/viajes_web", status_code=303)

    error_msg = None

    try:
        fecha_obj = datetime.strptime(fecha_salida, "%Y-%m-%d")
    except:
        error_msg = "Fecha de salida inválida (use YYYY-MM-DD)"

    if not error_msg and fecha_estimada:
        try:
            fecha_est_obj = datetime.strptime(fecha_estimada, "%Y-%m-%d")
            fecha_salida_obj = datetime.strptime(fecha_salida, "%Y-%m-%d")
            if fecha_est_obj.date() < fecha_salida_obj.date():
                error_msg = "La fecha estimada no puede ser anterior a la fecha de salida"
        except:
            error_msg = "Fecha estimada inválida (use YYYY-MM-DD)"

    if not error_msg:
        if estado not in ['pendiente', 'en progreso', 'completado', 'cancelado']:
            error_msg = "Estado no válido"

    if not error_msg and id_conductor:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id_conductor FROM conductor WHERE id_conductor=%s", (id_conductor,))
        if not cursor.fetchone():
            db.close()
            error_msg = "Conductor seleccionado no existe"
        else:
            db.close()

    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM viaje WHERE id_viaje=%s", (id,))
        viaje = cursor.fetchone()
        cursor.execute("SELECT id_conductor, nombre, apellido FROM conductor ORDER BY nombre, apellido")
        conductores_list = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("viajes_edit.html", {
            "request": request,
            "viaje": viaje,
            "usuario": usuario,
            "conductores_list": conductores_list,
            "error": error_msg
        })

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE viaje SET origen=%s, destino=%s, fecha_salida=%s, fecha_estimada=%s, estado=%s, id_conductor=%s WHERE id_viaje=%s",
            (origen, destino, fecha_salida, fecha_estimada if fecha_estimada else None, estado, id_conductor if id_conductor else None, id)
        )
        db.commit()
        db.close()
        
        # Registrar log
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "modificar",
            "viaje",
            id,
            f"Viaje {origen} → {destino}"
        )
        
        return RedirectResponse("/viajes_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM viaje WHERE id_viaje=%s", (id,))
        viaje = cursor2.fetchone()
        cursor2.execute("SELECT id_conductor, nombre, apellido FROM conductor ORDER BY nombre, apellido")
        conductores_list = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("viajes_edit.html", {
            "request": request,
            "viaje": viaje,
            "usuario": usuario,
            "conductores_list": conductores_list,
            "error": f"Error al actualizar viaje: {str(e)}"
        })

# ==================== MANTENIMIENTO ====================
@app.get("/mantenimiento_web")
def mantenimiento_web(request: Request, buscar: str = "", filtro_vehiculo: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = """
        SELECT m.id_mantenimiento, m.id_vehiculo, m.tipo, m.descripcion, m.costo, m.fecha,
               v.matricula
        FROM mantenimiento m
        JOIN vehiculo v ON v.id_vehiculo = m.id_vehiculo
        WHERE 1=1
    """
    params = []
    
    # Si es conductor, solo ve mantenimiento de sus vehículos
    if usuario.get("rol") == "conductor":
        id_conductor = usuario.get("id_conductor")
        if id_conductor:
            query += " AND v.id_conductor = %s"
            params.append(id_conductor)
        else:
            query += " AND 1=0"
    
    if buscar:
        query += " AND m.descripcion LIKE %s"
        params.append(f"%{buscar}%")
    
    if filtro_vehiculo:
        query += " AND v.id_vehiculo = %s"
        params.append(filtro_vehiculo)
    
    query += " ORDER BY m.fecha DESC, m.id_mantenimiento DESC"
    cursor.execute(query, params)
    mant = cursor.fetchall()
    
    # Lista de vehículos para el filtro
    vehiculos_query = "SELECT id_vehiculo, matricula FROM vehiculo WHERE 1=1"
    vehiculos_params = []
    if usuario.get("rol") == "conductor":
        id_conductor = usuario.get("id_conductor")
        if id_conductor:
            vehiculos_query += " AND id_conductor = %s"
            vehiculos_params.append(id_conductor)
    
    vehiculos_query += " ORDER BY matricula"
    cursor.execute(vehiculos_query, vehiculos_params)
    vehiculos_list = cursor.fetchall()
    db.close()
    
    return templates.TemplateResponse("mantenimiento.html", {
        "request": request, 
        "mantenimiento": mant, 
        "usuario": usuario,
        "buscar": buscar,
        "filtro_vehiculo": filtro_vehiculo,
        "vehiculos_list": vehiculos_list,
        "error": ""
    })

@app.post("/mantenimiento_create")
def mantenimiento_create(request: Request, id_vehiculo: int = Form(...), tipo: str = Form(...), descripcion: str = Form(...), costo: float = Form(...), fecha: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] not in ["admin", "mecanico"]:
        return RedirectResponse("/mantenimiento_web", status_code=303)
    
    error_msg = None
    
    if not id_vehiculo or id_vehiculo < 1:
        error_msg = "Debe seleccionar un vehículo válido"
    elif tipo not in ['preventivo', 'correctivo', 'reparacion']:
        error_msg = "El tipo de mantenimiento no es válido"
    elif not descripcion or len(descripcion) < 5 or len(descripcion) > 255:
        error_msg = "La descripción debe tener entre 5 y 255 caracteres"
    elif costo < 0 or costo > 9999999.99:
        error_msg = "El costo debe estar entre 0 y 9,999,999.99"
    elif not fecha:
        error_msg = "La fecha es obligatoria"
    else:
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
            if fecha_obj.date() > datetime.now().date():
                error_msg = "La fecha de mantenimiento no puede ser en el futuro"
        except:
            error_msg = "Formato de fecha inválido (use YYYY-MM-DD)"
    
    if not error_msg:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id_vehiculo FROM vehiculo WHERE id_vehiculo=%s", (id_vehiculo,))
        if not cursor.fetchone():
            db.close()
            error_msg = "El vehículo seleccionado no existe"
        else:
            db.close()
    
    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.id_mantenimiento, m.id_vehiculo, m.tipo, m.descripcion, m.costo, m.fecha, v.matricula
            FROM mantenimiento m
            JOIN vehiculo v ON v.id_vehiculo = m.id_vehiculo
        """)
        mant = cursor.fetchall()
        cursor.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
        vehiculos_list = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("mantenimiento.html", {
            "request": request, 
            "mantenimiento": mant, 
            "usuario": usuario,
            "vehiculos_list": vehiculos_list,
            "error": error_msg
        })
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO mantenimiento (id_vehiculo, tipo, descripcion, costo, fecha) VALUES (%s,%s,%s,%s,%s)",
                       (id_vehiculo, tipo, descripcion, costo, fecha))
        mant_id = cursor.lastrowid
        db.commit()
        db.close()
        
        # Registrar log
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "crear",
            "mantenimiento",
            mant_id,
            f"Mantenimiento {tipo} - {descripcion[:50]}"
        )
        
        return RedirectResponse("/mantenimiento_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("""
            SELECT m.id_mantenimiento, m.id_vehiculo, m.tipo, m.descripcion, m.costo, m.fecha, v.matricula
            FROM mantenimiento m
            JOIN vehiculo v ON v.id_vehiculo = m.id_vehiculo
        """)
        mant = cursor2.fetchall()
        cursor2.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
        vehiculos_list = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("mantenimiento.html", {
            "request": request, 
            "mantenimiento": mant, 
            "usuario": usuario,
            "vehiculos_list": vehiculos_list,
            "error": f"Error al crear mantenimiento: {str(e)}"
        })

@app.get("/mantenimiento_edit/{id}")
def mantenimiento_edit(request: Request, id: int):
    usuario = request.session.get("usuario")
    # Solo admin puede editar
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/mantenimiento_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM mantenimiento WHERE id_mantenimiento=%s", (id,))
    mant = cursor.fetchone()
    cursor.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
    vehiculos_list = cursor.fetchall()
    db.close()
    
    if not mant:
        return RedirectResponse("/mantenimiento_web", status_code=303)
    
    return templates.TemplateResponse("mantenimiento_edit.html", {
        "request": request,
        "mantenimiento": mant,
        "vehiculos_list": vehiculos_list,
        "usuario": usuario,
        "error": ""
    })

@app.post("/mantenimiento_update/{id}")
def mantenimiento_update(request: Request, id: int, id_vehiculo: int = Form(...), tipo: str = Form(...), descripcion: str = Form(...), costo: float = Form(...), fecha: str = Form(...)):
    usuario = request.session.get("usuario")
    # Solo admin puede actualizar
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/mantenimiento_web", status_code=303)
    
    error_msg = None
    
    if not id_vehiculo or id_vehiculo < 1:
        error_msg = "Debe seleccionar un vehículo válido"
    elif tipo not in ['preventivo', 'correctivo', 'reparacion']:
        error_msg = "El tipo de mantenimiento no es válido"
    elif not descripcion or len(descripcion) < 5 or len(descripcion) > 255:
        error_msg = "La descripción debe tener entre 5 y 255 caracteres"
    elif costo < 0 or costo > 9999999.99:
        error_msg = "El costo debe estar entre 0 y 9,999,999.99"
    elif not fecha:
        error_msg = "La fecha es obligatoria"
    else:
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
            if fecha_obj.date() > datetime.now().date():
                error_msg = "La fecha de mantenimiento no puede ser en el futuro"
        except:
            error_msg = "Formato de fecha inválido (use YYYY-MM-DD)"
    
    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM mantenimiento WHERE id_mantenimiento=%s", (id,))
        mant = cursor.fetchone()
        cursor.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
        vehiculos_list = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("mantenimiento_edit.html", {
            "request": request,
            "mantenimiento": mant,
            "vehiculos_list": vehiculos_list,
            "usuario": usuario,
            "error": error_msg
        })
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""UPDATE mantenimiento
                          SET id_vehiculo=%s, tipo=%s, descripcion=%s, costo=%s, fecha=%s
                          WHERE id_mantenimiento=%s""",
                       (id_vehiculo, tipo, descripcion, costo, fecha, id))
        db.commit()
        db.close()
        
        # Registrar log
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "modificar",
            "mantenimiento",
            id,
            f"Mantenimiento {tipo} - {descripcion[:50]}"
        )
        
        return RedirectResponse("/mantenimiento_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM mantenimiento WHERE id_mantenimiento=%s", (id,))
        mant = cursor2.fetchone()
        cursor2.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
        vehiculos_list = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("mantenimiento_edit.html", {
            "request": request,
            "mantenimiento": mant,
            "vehiculos_list": vehiculos_list,
            "usuario": usuario,
            "error": f"Error al actualizar: {str(e)}"
        })

@app.get("/mantenimiento_delete/{id}")
def mantenimiento_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    # Solo admin puede eliminar
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/mantenimiento_web", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        # Obtener datos antes de eliminar
        cursor.execute("SELECT tipo, descripcion FROM mantenimiento WHERE id_mantenimiento=%s", (id,))
        mant = cursor.fetchone()
        
        cursor.execute("DELETE FROM mantenimiento WHERE id_mantenimiento=%s", (id,))
        db.commit()
        
        # Registrar log
        if mant:
            registrar_log(
                usuario["id_usuario"],
                usuario["nombre"],
                "eliminar",
                "mantenimiento",
                id,
                f"Mantenimiento {mant['tipo']} - {mant['descripcion'][:50]}"
            )
    except:
        db.rollback()
    finally:
        db.close()
    return RedirectResponse("/mantenimiento_web", status_code=303)

# ==================== CONSUMO ====================
@app.get("/consumo_web")
def consumo_web(request: Request, buscar: str = "", filtro_vehiculo: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM consumo WHERE 1=1"
    params = []
    
    # Si es conductor, solo ve consumo de sus vehículos
    if usuario.get("rol") == "conductor":
        id_conductor = usuario.get("id_conductor")
        if id_conductor:
            # Obtener las matrículas de los vehículos del conductor
            query = """
                SELECT c.* FROM consumo c
                JOIN vehiculo v ON v.matricula = c.matricula
                WHERE v.id_conductor = %s
            """
            params.append(id_conductor)
        else:
            query += " AND 1=0"
    
    if filtro_vehiculo:
        if usuario.get("rol") == "conductor":
            query += " AND v.id_vehiculo = %s"
        else:
            query += " AND c.matricula = (SELECT matricula FROM vehiculo WHERE id_vehiculo = %s)"
        params.append(filtro_vehiculo)
    
    if buscar:
        query += " AND c.matricula LIKE %s"
        params.append(f"%{buscar}%")
    
    query += " ORDER BY fecha DESC, id_consumo DESC"
    cursor.execute(query, params)
    cons = cursor.fetchall()
    
    # Lista de vehículos para el filtro
    vehiculos_query = "SELECT id_vehiculo, matricula FROM vehiculo WHERE 1=1"
    vehiculos_params = []
    if usuario.get("rol") == "conductor":
        id_conductor = usuario.get("id_conductor")
        if id_conductor:
            vehiculos_query += " AND id_conductor = %s"
            vehiculos_params.append(id_conductor)
    
    vehiculos_query += " ORDER BY matricula"
    cursor.execute(vehiculos_query, vehiculos_params)
    vehiculos_list = cursor.fetchall()
    db.close()
    
    return templates.TemplateResponse("consumo.html", {
        "request": request, 
        "consumo": cons, 
        "usuario": usuario,
        "filtro_vehiculo": filtro_vehiculo,
        "vehiculos_list": vehiculos_list,
        "buscar": buscar,
        "error": ""
    })

@app.post("/consumo_create")
def consumo_create(request: Request, matricula: str = Form(...), litros: float = Form(...), fecha: str = Form(...), tipo_combustible: str = Form(...), costo: float = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] not in ["admin", "mecanico"]:
        return RedirectResponse("/consumo_web", status_code=303)
    
    error_msg = None
    
    if not matricula:
        error_msg = "Debe seleccionar un vehículo válido"
    elif litros <= 0 or litros > 9999.99:
        error_msg = "Los litros deben estar entre 0.01 y 9,999.99"
    elif not fecha:
        error_msg = "La fecha es obligatoria"
    else:
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
            if fecha_obj.date() > datetime.now().date():
                error_msg = "La fecha de consumo no puede ser en el futuro"
        except:
            error_msg = "Formato de fecha inválido (use YYYY-MM-DD)"
    
    if not error_msg:
        if not tipo_combustible or len(tipo_combustible) > 30:
            error_msg = "Tipo de combustible inválido"
    
    if not error_msg:
        try:
            if costo < 0 or costo > 1000000:
                error_msg = "Costo inválido"
        except:
            error_msg = "Costo inválido"
    
    if not error_msg:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT matricula FROM vehiculo WHERE matricula=%s", (matricula,))
        if not cursor.fetchone():
            db.close()
            error_msg = "El vehículo seleccionado no existe"
        else:
            db.close()
    
    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM consumo")
        cons = cursor.fetchall()
        cursor.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
        vehiculos_list = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("consumo.html", {
            "request": request, 
            "consumo": cons, 
            "usuario": usuario,
            "vehiculos_list": vehiculos_list,
            "error": error_msg
        })
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO consumo (matricula, litros, fecha, tipo_combustible, costo) VALUES (%s,%s,%s,%s,%s)",
                       (matricula, litros, fecha, tipo_combustible, costo))
        consumo_id = cursor.lastrowid
        db.commit()
        db.close()
        
        # Registrar log
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "crear",
            "consumo",
            consumo_id,
            f"Consumo {matricula} - {litros}L {tipo_combustible}"
        )
        
        return RedirectResponse("/consumo_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM consumo")
        cons = cursor2.fetchall()
        cursor2.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
        vehiculos_list = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("consumo.html", {
            "request": request, 
            "consumo": cons, 
            "usuario": usuario,
            "vehiculos_list": vehiculos_list,
            "error": f"Error al crear consumo: {str(e)}"
        })

@app.get("/consumo_edit/{id}")
def consumo_edit(request: Request, id: int):
    usuario = request.session.get("usuario")
    # Solo admin puede editar
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/consumo_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM consumo WHERE id_consumo=%s", (id,))
    cons = cursor.fetchone()
    cursor.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
    vehiculos_list = cursor.fetchall()
    db.close()
    
    if not cons:
        return RedirectResponse("/consumo_web", status_code=303)
    
    return templates.TemplateResponse("consumo_edit.html", {
        "request": request,
        "consumo": cons,
        "vehiculos_list": vehiculos_list,
        "usuario": usuario,
        "error": ""
    })

@app.post("/consumo_update/{id}")
def consumo_update(request: Request, id: int, matricula: str = Form(...), litros: float = Form(...), fecha: str = Form(...), tipo_combustible: str = Form(...), costo: float = Form(...)):
    usuario = request.session.get("usuario")
    # Solo admin puede actualizar
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/consumo_web", status_code=303)
    
    error_msg = None
    
    if not matricula:
        error_msg = "Debe seleccionar un vehículo válido"
    elif litros <= 0 or litros > 9999.99:
        error_msg = "Los litros deben estar entre 0.01 y 9,999.99"
    elif not fecha:
        error_msg = "La fecha es obligatoria"
    else:
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
            if fecha_obj.date() > datetime.now().date():
                error_msg = "La fecha de consumo no puede ser en el futuro"
        except:
            error_msg = "Formato de fecha inválido (use YYYY-MM-DD)"
    
    if not error_msg:
        if not tipo_combustible or len(tipo_combustible) > 30:
            error_msg = "Tipo de combustible inválido"
    
    if not error_msg:
        try:
            if costo < 0 or costo > 1000000:
                error_msg = "Costo inválido"
        except:
            error_msg = "Costo inválido"
    
    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM consumo WHERE id_consumo=%s", (id,))
        cons = cursor.fetchone()
        cursor.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
        vehiculos_list = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("consumo_edit.html", {
            "request": request,
            "consumo": cons,
            "vehiculos_list": vehiculos_list,
            "usuario": usuario,
            "error": error_msg
        })
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""UPDATE consumo
                          SET matricula=%s, litros=%s, fecha=%s, tipo_combustible=%s, costo=%s
                          WHERE id_consumo=%s""",
                       (matricula, litros, fecha, tipo_combustible, costo, id))
        db.commit()
        db.close()
        
        # Registrar log
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "modificar",
            "consumo",
            id,
            f"Consumo {matricula} - {litros}L {tipo_combustible}"
        )
        
        return RedirectResponse("/consumo_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM consumo WHERE id_consumo=%s", (id,))
        cons = cursor2.fetchone()
        cursor2.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
        vehiculos_list = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("consumo_edit.html", {
            "request": request,
            "consumo": cons,
            "vehiculos_list": vehiculos_list,
            "usuario": usuario,
            "error": f"Error al actualizar: {str(e)}"
        })

@app.get("/consumo_delete/{id}")
def consumo_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    # Solo admin puede eliminar
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/consumo_web", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        # Obtener datos antes de eliminar
        cursor.execute("SELECT matricula, litros, tipo_combustible FROM consumo WHERE id_consumo=%s", (id,))
        consumo = cursor.fetchone()
        
        cursor.execute("DELETE FROM consumo WHERE id_consumo=%s", (id,))
        db.commit()
        
        # Registrar log
        if consumo:
            registrar_log(
                usuario["id_usuario"],
                usuario["nombre"],
                "eliminar",
                "consumo",
                id,
                f"Consumo {consumo['matricula']} - {consumo['litros']}L {consumo['tipo_combustible']}"
            )
    except:
        db.rollback()
    finally:
        db.close()
    return RedirectResponse("/consumo_web", status_code=303)

# ==================== FLOTA ====================
@app.get("/flota_web")
def flota_web(request: Request, buscar: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM flota WHERE 1=1"
    params = []
    
    # Si es conductor, solo ve la flota de sus vehículos
    if usuario.get("rol") == "conductor":
        id_conductor = usuario.get("id_conductor")
        if id_conductor:
            query = """
                SELECT DISTINCT f.* FROM flota f
                JOIN vehiculo v ON v.id_flota = f.id_flota
                WHERE v.id_conductor = %s OR v.id_conductor IS NULL
            """
            params.append(id_conductor)
        else:
            cursor.execute("SELECT * FROM flota WHERE 1=0")
            flotas = cursor.fetchall()
            db.close()
            return templates.TemplateResponse("flota.html", {
                "request": request, 
                "flota": flotas, 
                "usuario": usuario,
                "buscar": buscar
            })
    else:
        # Búsqueda por nombre (admin/otros roles)
        if buscar:
            query += " AND nombre LIKE %s"
            params.append(f"%{buscar}%")
    
    cursor.execute(query, params)
    flotas = cursor.fetchall()
    db.close()
    
    return templates.TemplateResponse("flota.html", {
        "request": request, 
        "flota": flotas, 
        "usuario": usuario,
        "buscar": buscar
    })

@app.post("/flota_create")
def flota_create(request: Request, nombre: str = Form(...), descripcion: str = Form(...), 
                 categoria: str = Form(...), ubicacion: str = Form(...), 
                 estado: str = Form(...), politica_uso: str = Form(None),
                 capacidad_maxima: int = Form(0), fecha_creacion: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/flota_web", status_code=303)
    
    # VALIDACIONES
    error_msg = None
    
    # Validar nombre
    if not nombre or len(nombre) < 2 or len(nombre) > 40:
        error_msg = "El nombre debe tener entre 2 y 40 caracteres"
    elif not all(c.isalnum() or c.isspace() or c == '-' for c in nombre):
        error_msg = "El nombre contiene caracteres inválidos"
    
    # Validar descripción
    elif not descripcion or len(descripcion) < 5 or len(descripcion) > 100:
        error_msg = "La descripción debe tener entre 5 y 100 caracteres"
    
    # Validar categoría
    elif categoria not in ['carga_ligera','carga_pesada','transporte_personal','reparto','especial']:
        error_msg = "Categoría inválida"
    
    # Validar ubicación
    elif not ubicacion or len(ubicacion) < 3 or len(ubicacion) > 100:
        error_msg = "La ubicación debe tener entre 3 y 100 caracteres"
    
    # Validar estado
    elif estado not in ['activa','inactiva','mantenimiento']:
        error_msg = "Estado inválido"
    
    # Validar capacidad
    elif capacidad_maxima < 0 or capacidad_maxima > 1000:
        error_msg = "La capacidad debe estar entre 0 y 1000"
    
    # Validar fecha
    elif not fecha_creacion:
        error_msg = "La fecha de creación es obligatoria"
    
    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM flota")
        flotas = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("flota.html", {
            "request": request, 
            "flota": flotas, 
            "usuario": usuario,
            "error": error_msg
        })
    
    db = get_db()
    cursor = db.cursor()
    
    # Validar que el nombre no exista
    cursor.execute("SELECT * FROM flota WHERE nombre=%s", (nombre,))
    if cursor.fetchone():
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM flota")
        flotas = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("flota.html", {
            "request": request, 
            "flota": flotas, 
            "usuario": usuario,
            "error": "Ya existe una flota con ese nombre"
        })
    
    try:
        cursor.execute("""
            INSERT INTO flota (nombre, descripcion, categoria, ubicacion, estado, politica_uso, capacidad_maxima, fecha_creacion) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (nombre, descripcion, categoria, ubicacion, estado, politica_uso, capacidad_maxima, fecha_creacion))
        flota_id = cursor.lastrowid
        db.commit()
        db.close()
        
        # Registrar log
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "crear",
            "flota",
            flota_id,
            f"Flota {nombre} - {categoria}"
        )
        
        return RedirectResponse("/flota_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM flota")
        flotas = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("flota.html", {
            "request": request, 
            "flota": flotas, 
            "usuario": usuario,
            "error": f"Error al crear flota: {str(e)}"
        })

@app.get("/flota_delete/{id}")
def flota_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/flota_web", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener datos antes de eliminar
    cursor.execute("SELECT nombre, categoria FROM flota WHERE id_flota=%s", (id,))
    flota = cursor.fetchone()
    
    cursor.execute("DELETE FROM flota WHERE id_flota=%s", (id,))
    db.commit()
    db.close()
    
    # Registrar log
    if flota:
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "eliminar",
            "flota",
            id,
            f"Flota {flota['nombre']} - {flota['categoria']}"
        )
    
    return RedirectResponse("/flota_web", status_code=303)

@app.get("/flota_edit/{id}")
def flota_edit(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/flota_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM flota WHERE id_flota=%s", (id,))
    flota = cursor.fetchone()
    db.close()
    
    if not flota:
        return RedirectResponse("/flota_web", status_code=303)
    
    return templates.TemplateResponse("flota_edit.html", {"request": request, "flota": flota, "usuario": usuario})

@app.post("/flota_update/{id}")
def flota_update(request: Request, id: int, nombre: str = Form(...), descripcion: str = Form(...),
                 categoria: str = Form(...), ubicacion: str = Form(...), 
                 estado: str = Form(...), politica_uso: str = Form(None),
                 capacidad_maxima: int = Form(0), fecha_creacion: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/flota_web", status_code=303)
    
    # VALIDACIONES
    error_msg = None
    
    # Validar nombre
    if not nombre or len(nombre) < 2 or len(nombre) > 40:
        error_msg = "El nombre debe tener entre 2 y 40 caracteres"
    elif not all(c.isalnum() or c.isspace() or c == '-' for c in nombre):
        error_msg = "El nombre contiene caracteres inválidos"
    
    # Validar descripción
    elif not descripcion or len(descripcion) < 5 or len(descripcion) > 100:
        error_msg = "La descripción debe tener entre 5 y 100 caracteres"
    
    # Validar categoría
    elif categoria not in ['carga_ligera','carga_pesada','transporte_personal','reparto','especial']:
        error_msg = "Categoría inválida"
    
    # Validar ubicación
    elif not ubicacion or len(ubicacion) < 3 or len(ubicacion) > 100:
        error_msg = "La ubicación debe tener entre 3 y 100 caracteres"
    
    # Validar estado
    elif estado not in ['activa','inactiva','mantenimiento']:
        error_msg = "Estado inválido"
    
    # Validar capacidad
    elif capacidad_maxima < 0 or capacidad_maxima > 1000:
        error_msg = "La capacidad debe estar entre 0 y 1000"
    
    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM flota WHERE id_flota=%s", (id,))
        flota = cursor.fetchone()
        db.close()
        return templates.TemplateResponse("flota_edit.html", {
            "request": request,
            "flota": flota,
            "usuario": usuario,
            "error": error_msg
        })
    
    db = get_db()
    cursor = db.cursor()
    
    # Validar que el nombre no exista (excepto la flota actual)
    cursor.execute("SELECT * FROM flota WHERE nombre=%s AND id_flota!=%s", (nombre, id))
    if cursor.fetchone():
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM flota WHERE id_flota=%s", (id,))
        flota = cursor2.fetchone()
        db2.close()
        return templates.TemplateResponse("flota_edit.html", {
            "request": request,
            "flota": flota,
            "usuario": usuario,
            "error": "Ya existe otra flota con ese nombre"
        })
    
    try:
        cursor.execute("""
            UPDATE flota 
            SET nombre=%s, descripcion=%s, categoria=%s, ubicacion=%s, 
                estado=%s, politica_uso=%s, capacidad_maxima=%s, fecha_creacion=%s 
            WHERE id_flota=%s
        """, (nombre, descripcion, categoria, ubicacion, estado, politica_uso, capacidad_maxima, fecha_creacion, id))
        db.commit()
        db.close()
        
        # Registrar log
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "modificar",
            "flota",
            id,
            f"Flota {nombre} - {categoria}"
        )
        
        return RedirectResponse("/flota_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM flota WHERE id_flota=%s", (id,))
        flota = cursor2.fetchone()
        db2.close()
        return templates.TemplateResponse("flota_edit.html", {
            "request": request,
            "flota": flota,
            "usuario": usuario,
            "error": "Error al actualizar flota"
        })
    
# ==================== INCIDENTES ====================
@app.get("/incidentes_web")
def incidentes_web(request: Request, buscar: str = "", filtro_tipo: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM incidente WHERE 1=1"
    params = []
    
    # Si es conductor, solo ve incidentes de sus vehículos
    if usuario.get("rol") == "conductor":
        id_conductor = usuario.get("id_conductor")
        if id_conductor:
            query = """
                SELECT i.* FROM incidente i
                JOIN vehiculo v ON v.matricula = i.matricula
                WHERE v.id_conductor = %s
            """
            params.append(id_conductor)
        else:
            query += " AND 1=0"
    
    if buscar:
        query += " AND i.descripcion LIKE %s"
        params.append(f"%{buscar}%")
    
    if filtro_tipo:
        query += " AND i.tipo = %s"
        params.append(filtro_tipo)
    
    query += " ORDER BY fecha DESC, id_incidente DESC"
    cursor.execute(query, params)
    inc = cursor.fetchall()
    
    # Lista de vehículos para el filtro
    vehiculos_query = "SELECT id_vehiculo, matricula FROM vehiculo WHERE 1=1"
    vehiculos_params = []
    if usuario.get("rol") == "conductor":
        id_conductor = usuario.get("id_conductor")
        if id_conductor:
            vehiculos_query += " AND id_conductor = %s"
            vehiculos_params.append(id_conductor)
    
    vehiculos_query += " ORDER BY matricula"
    cursor.execute(vehiculos_query, vehiculos_params)
    vehiculos_list = cursor.fetchall()
    db.close()
    
    return templates.TemplateResponse("incidentes.html", {
        "request": request, 
        "incidentes": inc, 
        "usuario": usuario,
        "buscar": buscar,
        "filtro_tipo": filtro_tipo,
        "vehiculos_list": vehiculos_list,
        "error": ""
    })

@app.post("/incidentes_create")
def incidentes_create(request: Request, matricula: str = Form(...), tipo: str = Form(...), fecha: str = Form(...), descripcion: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] not in ["admin", "mecanico"]:
        return RedirectResponse("/incidentes_web", status_code=303)
    
    error_msg = None
    
    if not matricula:
        error_msg = "Debe seleccionar un vehículo válido"
    elif tipo not in ['accidente', 'infracción', 'daño', 'retraso', 'otro']:
        error_msg = "El tipo de incidente no es válido"
    elif not descripcion or len(descripcion) < 5 or len(descripcion) > 255:
        error_msg = "La descripción debe tener entre 5 y 255 caracteres"
    elif not fecha:
        error_msg = "La fecha es obligatoria"
    else:
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
            if fecha_obj.date() > datetime.now().date():
                error_msg = "La fecha del incidente no puede ser en el futuro"
        except:
            error_msg = "Formato de fecha inválido (use YYYY-MM-DD)"
    
    if not error_msg:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT matricula FROM vehiculo WHERE matricula=%s", (matricula,))
        if not cursor.fetchone():
            db.close()
            error_msg = "El vehículo seleccionado no existe"
        else:
            db.close()
    
    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM incidente")
        inc = cursor.fetchall()
        cursor.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
        vehiculos_list = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("incidentes.html", {
            "request": request, 
            "incidentes": inc, 
            "usuario": usuario,
            "vehiculos_list": vehiculos_list,
            "error": error_msg
        })
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO incidente (matricula, tipo, fecha, descripcion) VALUES (%s,%s,%s,%s)",
                       (matricula, tipo, fecha, descripcion))
        db.commit()
        db.close()
        return RedirectResponse("/incidentes_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM incidente")
        inc = cursor2.fetchall()
        cursor2.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
        vehiculos_list = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("incidentes.html", {
            "request": request, 
            "incidentes": inc, 
            "usuario": usuario,
            "vehiculos_list": vehiculos_list,
            "error": f"Error al crear incidente: {str(e)}"
        })

@app.get("/incidentes_edit/{id}")
def incidentes_edit(request: Request, id: int):
    usuario = request.session.get("usuario")
    # Solo admin puede editar
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/incidentes_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM incidente WHERE id_incidente=%s", (id,))
    inc = cursor.fetchone()
    cursor.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
    vehiculos_list = cursor.fetchall()
    db.close()
    
    if not inc:
        return RedirectResponse("/incidentes_web", status_code=303)
    
    return templates.TemplateResponse("incidentes_edit.html", {
        "request": request,
        "incidente": inc,
        "vehiculos_list": vehiculos_list,
        "usuario": usuario,
        "error": ""
    })

@app.post("/incidentes_update/{id}")
def incidentes_update(request: Request, id: int, matricula: str = Form(...), tipo: str = Form(...), fecha: str = Form(...), descripcion: str = Form(...)):
    usuario = request.session.get("usuario")
    # Solo admin puede actualizar
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/incidentes_web", status_code=303)
    
    error_msg = None
    
    if not matricula:
        error_msg = "Debe seleccionar un vehículo válido"
    elif tipo not in ['accidente', 'infracción', 'daño', 'retraso', 'otro']:
        error_msg = "El tipo de incidente no es válido"
    elif not descripcion or len(descripcion) < 5 or len(descripcion) > 255:
        error_msg = "La descripción debe tener entre 5 y 255 caracteres"
    elif not fecha:
        error_msg = "La fecha es obligatoria"
    else:
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
            if fecha_obj.date() > datetime.now().date():
                error_msg = "La fecha del incidente no puede ser en el futuro"
        except:
            error_msg = "Formato de fecha inválido (use YYYY-MM-DD)"
    
    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM incidente WHERE id_incidente=%s", (id,))
        inc = cursor.fetchone()
        cursor.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
        vehiculos_list = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("incidentes_edit.html", {
            "request": request,
            "incidente": inc,
            "vehiculos_list": vehiculos_list,
            "usuario": usuario,
            "error": error_msg
        })
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""UPDATE incidente
                          SET matricula=%s, tipo=%s, fecha=%s, descripcion=%s
                          WHERE id_incidente=%s""",
                       (matricula, tipo, fecha, descripcion, id))
        db.commit()
        db.close()
        return RedirectResponse("/incidentes_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM incidente WHERE id_incidente=%s", (id,))
        inc = cursor2.fetchone()
        cursor2.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
        vehiculos_list = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("incidentes_edit.html", {
            "request": request,
            "incidente": inc,
            "vehiculos_list": vehiculos_list,
            "usuario": usuario,
            "error": f"Error al actualizar: {str(e)}"
        })

@app.get("/incidentes_delete/{id}")
def incidentes_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    # Solo admin puede eliminar
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/incidentes_web", status_code=303)
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM incidente WHERE id_incidente=%s", (id,))
        db.commit()
    except:
        db.rollback()
    finally:
        db.close()
    return RedirectResponse("/incidentes_web", status_code=303)

# ==================== ORDENES ====================
@app.get("/ordenes_web")
def ordenes_web(request: Request, buscar: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM orden_servicio WHERE 1=1"
    params = []
    
    # Si es conductor, solo ve órdenes asignadas a sus viajes
    if usuario.get("rol") == "conductor":
        id_conductor = usuario.get("id_conductor")
        if id_conductor:
            query = """
                SELECT DISTINCT o.* FROM orden_servicio o
                JOIN viaje v ON v.id_orden = o.id_orden
                WHERE v.id_conductor = %s
            """
            params.append(id_conductor)
        else:
            query += " AND 1=0"
    
    # Búsqueda por descripción (solo para admin/logistica)
    if buscar and usuario.get("rol") not in ["conductor"]:
        query += " AND descripcion LIKE %s"
        params.append(f"%{buscar}%")
    elif buscar and usuario.get("rol") == "conductor":
        # Para conductores, la búsqueda es en órdenes asignadas
        query += " AND o.descripcion LIKE %s"
        params.append(f"%{buscar}%")
    
    cursor.execute(query, params)
    ordenes = cursor.fetchall()
    db.close()
    
    return templates.TemplateResponse("ordenes.html", {
        "request": request, 
        "ordenes": ordenes, 
        "usuario": usuario,
        "buscar": buscar
    })

@app.post("/ordenes_create")
def ordenes_create(request: Request, descripcion: str = Form(...), fecha: str = Form(...), estado: str = Form("pendiente")):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] not in ["admin", "logistica"]:
        return RedirectResponse("/ordenes_web", status_code=303)

    # VALIDACIONES
    error_msg = None

    # Validar descripción
    if not descripcion or len(descripcion) < 5 or len(descripcion) > 255:
        error_msg = "La descripción debe tener entre 5 y 255 caracteres"
    elif not all(c.isalnum() or c.isspace() or c in ['-', '.', ',', '(', ')', ':', ';'] for c in descripcion):
        error_msg = "La descripción contiene caracteres inválidos"

    # Validar fecha
    elif not fecha:
        error_msg = "La fecha es obligatoria"
    else:
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
            if fecha_obj.date() > datetime.now().date():
                error_msg = "La fecha de la orden no puede ser en el futuro"
        except:
            error_msg = "Formato de fecha inválido (use YYYY-MM-DD)"

    # Validar estado
    allowed_estados = ['pendiente', 'en progreso', 'completado', 'cancelado']
    if not error_msg:
        if estado not in allowed_estados:
            error_msg = "Estado no válido"

    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM orden_servicio")
        ordenes = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("ordenes.html", {
            "request": request,
            "ordenes": ordenes,
            "usuario": usuario,
            "error": error_msg
        })

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO orden_servicio (descripcion, fecha, estado) VALUES (%s,%s,%s)",
                       (descripcion, fecha, estado))
        orden_id = cursor.lastrowid
        db.commit()
        db.close()
        
        # Registrar log
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "crear",
            "orden_servicio",
            orden_id,
            f"Orden: {descripcion[:50]}"
        )
        
        return RedirectResponse("/ordenes_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM orden_servicio")
        ordenes = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("ordenes.html", {
            "request": request,
            "ordenes": ordenes,
            "usuario": usuario,
            "error": f"Error al crear orden: {str(e)}"
        })
    
@app.get("/ordenes_delete/{id}")
def ordenes_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/ordenes_web", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener datos antes de eliminar
    cursor.execute("SELECT descripcion FROM orden_servicio WHERE id_orden=%s", (id,))
    orden = cursor.fetchone()
    
    cursor.execute("DELETE FROM orden_servicio WHERE id_orden=%s", (id,))
    db.commit()
    db.close()
    
    # Registrar log
    if orden:
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "eliminar",
            "orden_servicio",
            id,
            f"Orden: {orden['descripcion'][:50]}"
        )
    
    return RedirectResponse("/ordenes_web", status_code=303)

@app.get("/ordenes_edit/{id}")
def ordenes_edit(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] not in ["admin", "logistica"]:
        return RedirectResponse("/ordenes_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orden_servicio WHERE id_orden=%s", (id,))
    orden = cursor.fetchone()
    db.close()
    
    if not orden:
        return RedirectResponse("/ordenes_web", status_code=303)
    
    return templates.TemplateResponse("ordenes_edit.html", {"request": request, "orden": orden, "usuario": usuario, "error": ""})

@app.post("/ordenes_update/{id}")
def ordenes_update(request: Request, id: int, descripcion: str = Form(...), fecha: str = Form(...), estado: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] not in ["admin", "logistica"]:
        return RedirectResponse("/ordenes_web", status_code=303)

    # VALIDACIONES
    error_msg = None

    # Validar descripción
    if not descripcion or len(descripcion) < 5 or len(descripcion) > 255:
        error_msg = "La descripción debe tener entre 5 y 255 caracteres"
    elif not all(c.isalnum() or c.isspace() or c in ['-', '.', ',', '(', ')', ':', ';'] for c in descripcion):
        error_msg = "La descripción contiene caracteres inválidos"
    
    # Validar fecha
    elif not fecha:
        error_msg = "La fecha es obligatoria"
    else:
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except:
            error_msg = "Formato de fecha inválido (use YYYY-MM-DD)"

    # Validar estado
    allowed_estados = ['pendiente', 'en progreso', 'completado', 'cancelado']
    if not error_msg:
        if estado not in allowed_estados:
            error_msg = "El estado no es válido"

    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM orden_servicio WHERE id_orden=%s", (id,))
        orden = cursor.fetchone()
        db.close()
        return templates.TemplateResponse("ordenes_edit.html", {
            "request": request,
            "orden": orden,
            "usuario": usuario,
            "error": error_msg
        })

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE orden_servicio SET descripcion=%s, fecha=%s, estado=%s WHERE id_orden=%s",
            (descripcion, fecha, estado, id)
        )
        db.commit()
        db.close()
        
        # Registrar log
        registrar_log(
            usuario["id_usuario"],
            usuario["nombre"],
            "modificar",
            "orden_servicio",
            id,
            f"Orden: {descripcion[:50]}"
        )
        
        return RedirectResponse("/ordenes_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM orden_servicio WHERE id_orden=%s", (id,))
        orden = cursor2.fetchone()
        db2.close()
        return templates.TemplateResponse("ordenes_edit.html", {
            "request": request,
            "orden": orden,
            "usuario": usuario,
            "error": f"Error al actualizar: {str(e)}"
        })
  
# ==================== LICENCIAS ====================
@app.get("/licencias_web")
def licencias_web(request: Request, buscar: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)

    db = get_db()
    if not db:
        return templates.TemplateResponse("licencias.html", {
            "request": request,
            "licencias": [],
            "conductores": [],
            "usuario": usuario,
            "buscar": buscar,
            "error": "No se pudo conectar a la base de datos."
        })

    cursor = db.cursor(dictionary=True)

    # obtener lista de conductores para el select (útil para admin)
    conductores = []
    try:
        cursor.execute("SELECT id_conductor, nombre, apellido FROM conductor ORDER BY nombre, apellido")
        conductores = cursor.fetchall()
    except Exception:
        conductores = []

    # construir consulta de licencias
    params = []
    query = """
        SELECT l.id_licencia, l.id_conductor, l.tipo, l.fecha_emision, l.fecha_vencimiento,
               c.nombre AS nombre_conductor, c.apellido AS apellido_conductor
        FROM licencia l
        JOIN conductor c ON c.id_conductor = l.id_conductor
        WHERE 1=1
    """

    if buscar:
        query += " AND (l.tipo LIKE %s OR c.nombre LIKE %s OR c.apellido LIKE %s)"
        term = f"%{buscar}%"
        params.extend([term, term, term])

    # si es conductor, limitar a sus licencias (se asume request.session["usuario"]["id_conductor"] si existe)
    if usuario.get("rol") == "conductor":
        id_conductor_usuario = usuario.get("id_conductor")
        if id_conductor_usuario:
            query += " AND l.id_conductor = %s"
            params.append(id_conductor_usuario)

    query += " ORDER BY l.id_licencia DESC"

    try:
        cursor.execute(query, params)
        licencias = cursor.fetchall()
    except Exception:
        licencias = []
    finally:
        db.close()

    return templates.TemplateResponse("licencias.html", {
        "request": request,
        "licencias": licencias,
        "conductores": conductores,
        "usuario": usuario,
        "buscar": buscar,
        "error": ""
    })

@app.post("/licencias_create")
def licencias_create(request: Request, id_conductor: int = Form(...), tipo: str = Form(...), fecha_emision: str = Form(...), fecha_vencimiento: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario.get("rol") != "admin":
        return RedirectResponse("/licencias_web", status_code=303)

    # validaciones básicas
    error = None
    
    # validar tipo enum
    tipos_validos = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'AM', 'A1', 'A2', 'B1']
    if tipo not in tipos_validos:
        error = f"Tipo inválido. Opciones válidas: {', '.join(tipos_validos)}"
    
    if error is None:
        try:
            fe = datetime.strptime(fecha_emision, "%Y-%m-%d").date()
            fv = datetime.strptime(fecha_vencimiento, "%Y-%m-%d").date()
            if fv <= fe:
                error = "La fecha de vencimiento debe ser posterior a la fecha de emisión."
        except Exception:
            error = "Formato de fecha inválido. Use YYYY-MM-DD."

    if error:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT l.id_licencia, l.id_conductor, l.tipo, l.fecha_emision, l.fecha_vencimiento, c.nombre AS nombre_conductor, c.apellido AS apellido_conductor FROM licencia l JOIN conductor c ON c.id_conductor = l.id_conductor")
        licencias = cursor.fetchall()
        cursor.execute("SELECT id_conductor, nombre, apellido FROM conductor ORDER BY nombre, apellido")
        conductores = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("licencias.html", {
            "request": request,
            "licencias": licencias,
            "conductores": conductores,
            "usuario": usuario,
            "buscar": "",
            "error": error
        })

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO licencia (id_conductor, tipo, fecha_emision, fecha_vencimiento) VALUES (%s,%s,%s,%s)",
                       (id_conductor, tipo, fecha_emision, fecha_vencimiento))
        db.commit()
    except mysql.connector.Error as e:
        db.rollback()
        db.close()
        return templates.TemplateResponse("licencias.html", {
            "request": request,
            "licencias": [],
            "conductores": [],
            "usuario": usuario,
            "buscar": "",
            "error": f"Error al insertar: {e}"
        })
    db.close()
    return RedirectResponse("/licencias_web", status_code=303)

@app.get("/licencias_delete/{id}")
def licencias_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario.get("rol") != "admin":
        return RedirectResponse("/licencias_web", status_code=303)

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM licencia WHERE id_licencia=%s", (id,))
        db.commit()
    except mysql.connector.Error:
        db.rollback()
    finally:
        db.close()
    return RedirectResponse("/licencias_web", status_code=303)

@app.get("/licencias_edit/{id}")
def licencias_edit(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario.get("rol") != "admin":
        return RedirectResponse("/licencias_web", status_code=303)

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM licencia WHERE id_licencia=%s", (id,))
    licencia = cursor.fetchone()

    # obtener lista de conductores para el select
    cursor.execute("SELECT id_conductor, nombre, apellido FROM conductor ORDER BY nombre, apellido")
    conductores = cursor.fetchall()
    db.close()

    if not licencia:
        return RedirectResponse("/licencias_web", status_code=303)

    return templates.TemplateResponse("licencias_edit.html", {
        "request": request, 
        "licencia": licencia, 
        "conductores": conductores, 
        "usuario": usuario, 
        "error": ""
    })

@app.post("/licencias_update/{id}")
def licencias_update(request: Request, id: int, id_conductor: int = Form(...), tipo: str = Form(...), fecha_emision: str = Form(...), fecha_vencimiento: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario.get("rol") != "admin":
        return RedirectResponse("/licencias_web", status_code=303)

    # validaciones
    error = None
    tipos_validos = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'AM', 'A1', 'A2', 'B1']
    if tipo not in tipos_validos:
        error = f"Tipo inválido. Opciones válidas: {', '.join(tipos_validos)}"
    
    if error is None:
        try:
            fe = datetime.strptime(fecha_emision, "%Y-%m-%d").date()
            fv = datetime.strptime(fecha_vencimiento, "%Y-%m-%d").date()
            if fv <= fe:
                error = "La fecha de vencimiento debe ser posterior."
        except Exception:
            error = "Formato de fecha inválido. Use YYYY-MM-DD."

    if error:
        # volver a formulario de edición con mensaje
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM licencia WHERE id_licencia=%s", (id,))
        licencia = cursor.fetchone()
        cursor.execute("SELECT id_conductor, nombre, apellido FROM conductor ORDER BY nombre, apellido")
        conductores = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("licencias_edit.html", {
            "request": request, 
            "licencia": licencia, 
            "conductores": conductores, 
            "usuario": usuario, 
            "error": error
        })

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""UPDATE licencia
                          SET id_conductor=%s, tipo=%s, fecha_emision=%s, fecha_vencimiento=%s
                          WHERE id_licencia=%s""",
                       (id_conductor, tipo, fecha_emision, fecha_vencimiento, id))
        db.commit()
    except mysql.connector.Error as e:
        db.rollback()
    finally:
        db.close()

    return RedirectResponse("/licencias_web", status_code=303)

# ==================== EVALUACIONES ====================
@app.get("/evaluaciones_web")
def evaluaciones_web(request: Request, buscar: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)

    db = get_db()
    if not db:
        return templates.TemplateResponse("evaluaciones.html", {
            "request": request,
            "evaluaciones": [],
            "conductores": [],
            "usuario": usuario,
            "buscar": buscar,
            "error": "No se pudo conectar a la base de datos."
        })

    cursor = db.cursor(dictionary=True)

    # lista de conductores para el select (admin/logistica)
    conductores = []
    try:
        cursor.execute("SELECT id_conductor, nombre, apellido FROM conductor ORDER BY nombre, apellido")
        conductores = cursor.fetchall()
    except:
        conductores = []

    params = []
    query = """
        SELECT e.id_evaluacion, e.id_conductor, e.fecha, e.puntuacion, e.comentarios,
               c.nombre AS nombre_conductor, c.apellido AS apellido_conductor
        FROM evaluacion e
        JOIN conductor c ON c.id_conductor = e.id_conductor
        WHERE 1=1
    """

    if buscar:
        query += " AND (c.nombre LIKE %s OR c.apellido LIKE %s OR e.comentarios LIKE %s)"
        term = f"%{buscar}%"
        params.extend([term, term, term])

    # conductor solo ve sus evaluaciones (si tiene id_conductor en session)
    if usuario.get("rol") == "conductor":
        id_conductor_usuario = usuario.get("id_conductor")
        if id_conductor_usuario:
            query += " AND e.id_conductor = %s"
            params.append(id_conductor_usuario)

    query += " ORDER BY e.id_evaluacion DESC"

    try:
        cursor.execute(query, params)
        evaluaciones = cursor.fetchall()
    except:
        evaluaciones = []
    finally:
        db.close()

    return templates.TemplateResponse("evaluaciones.html", {
        "request": request,
        "evaluaciones": evaluaciones,
        "conductores": conductores,
        "usuario": usuario,
        "buscar": buscar,
        "error": ""
    })

@app.post("/evaluaciones_create")
def evaluaciones_create(request: Request, id_conductor: int = Form(...), fecha: str = Form(...), puntuacion: int = Form(...), comentarios: str = Form(None)):
    usuario = request.session.get("usuario")
    if not usuario or usuario.get("rol") not in ["admin", "logistica"]:
        return RedirectResponse("/evaluaciones_web", status_code=303)

    error = None
    # fecha valida
    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    except:
        error = "Fecha inválida. Use YYYY-MM-DD."

    # puntuacion valida
    if error is None:
        try:
            p = int(puntuacion)
            if p < 1 or p > 10:
                error = "La puntuación debe estar entre 1 y 10."
        except:
            error = "Puntuación inválida."

    # validar conductor existe
    if error is None:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id_conductor FROM conductor WHERE id_conductor=%s", (id_conductor,))
        if not cursor.fetchone():
            db.close()
            error = "Conductor no existe"
        else:
            db.close()

    if error:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""SELECT e.id_evaluacion, e.id_conductor, e.fecha, e.puntuacion, e.comentarios,
                                 c.nombre AS nombre_conductor, c.apellido AS apellido_conductor
                          FROM evaluacion e JOIN conductor c ON c.id_conductor = e.id_conductor""")
        evaluaciones = cursor.fetchall()
        cursor.execute("SELECT id_conductor, nombre, apellido FROM conductor ORDER BY nombre, apellido")
        conductores = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("evaluaciones.html", {
            "request": request,
            "evaluaciones": evaluaciones,
            "conductores": conductores,
            "usuario": usuario,
            "buscar": "",
            "error": error
        })

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO evaluacion (id_conductor, fecha, puntuacion, comentarios) VALUES (%s,%s,%s,%s)",
                       (id_conductor, fecha, puntuacion, comentarios))
        db.commit()
    except Exception as e:
        db.rollback()
        db.close()
        return templates.TemplateResponse("evaluaciones.html", {
            "request": request,
            "evaluaciones": [],
            "conductores": [],
            "usuario": usuario,
            "buscar": "",
            "error": f"Error al insertar: {str(e)}"
        })
    db.close()
    return RedirectResponse("/evaluaciones_web", status_code=303)

@app.get("/evaluaciones_delete/{id}")
def evaluaciones_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario.get("rol") not in ["admin", "logistica"]:
        return RedirectResponse("/evaluaciones_web", status_code=303)

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM evaluacion WHERE id_evaluacion=%s", (id,))
        db.commit()
    except:
        db.rollback()
    finally:
        db.close()
    return RedirectResponse("/evaluaciones_web", status_code=303)

@app.get("/evaluaciones_edit/{id}")
def evaluaciones_edit(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario.get("rol") not in ["admin", "logistica"]:
        return RedirectResponse("/evaluaciones_web", status_code=303)

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM evaluacion WHERE id_evaluacion=%s", (id,))
    evaluacion = cursor.fetchone()
    cursor.execute("SELECT id_conductor, nombre, apellido FROM conductor ORDER BY nombre, apellido")
    conductores = cursor.fetchall()
    db.close()

    if not evaluacion:
        return RedirectResponse("/evaluaciones_web", status_code=303)

    return templates.TemplateResponse("evaluaciones_edit.html", {
        "request": request,
        "evaluacion": evaluacion,
        "conductores": conductores,
        "usuario": usuario,
        "error": ""
    })

@app.post("/evaluaciones_update/{id}")
def evaluaciones_update(request: Request, id: int, id_conductor: int = Form(...), fecha: str = Form(...), puntuacion: int = Form(...), comentarios: str = Form(None)):
    usuario = request.session.get("usuario")
    if not usuario or usuario.get("rol") not in ["admin", "logistica"]:
        return RedirectResponse("/evaluaciones_web", status_code=303)

    error = None
    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    except:
        error = "Fecha inválida. Use YYYY-MM-DD."

    if error is None:
        try:
            p = int(puntuacion)
            if p < 1 or p > 10:
                error = "La puntuación debe estar entre 1 y 10."
        except:
            error = "Puntuación inválida."

    # validar conductor
    if error is None:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id_conductor FROM conductor WHERE id_conductor=%s", (id_conductor,))
        if not cursor.fetchone():
            db.close()
            error = "Conductor no existe"
        else:
            db.close()

    if error:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM evaluacion WHERE id_evaluacion=%s", (id,))
        evaluacion = cursor.fetchone()
        cursor.execute("SELECT id_conductor, nombre, apellido FROM conductor ORDER BY nombre, apellido")
        conductores = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("evaluaciones_edit.html", {
            "request": request,
            "evaluacion": evaluacion,
            "conductores": conductores,
            "usuario": usuario,
            "error": error
        })

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""UPDATE evaluacion
                          SET id_conductor=%s, fecha=%s, puntuacion=%s, comentarios=%s
                          WHERE id_evaluacion=%s""",
                       (id_conductor, fecha, puntuacion, comentarios, id))
        db.commit()
    except:
        db.rollback()
    finally:
        db.close()

    return RedirectResponse("/evaluaciones_web", status_code=303)

# ==================== USUARIOS ====================
@app.get("/usuarios_web")
def usuarios_web(request: Request, buscar: str = ""):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/home", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM usuario WHERE 1=1"
    params = []
    
    if buscar:
        query += " AND (nombre LIKE %s OR correo LIKE %s OR rol LIKE %s)"
        params.extend([f"%{buscar}%", f"%{buscar}%", f"%{buscar}%"])
    
    cursor.execute(query, params)
    usuarios = cursor.fetchall()
    db.close()
    return templates.TemplateResponse("usuarios.html", {
        "request": request, 
        "usuarios": usuarios, 
        "usuario": usuario,
        "buscar": buscar,
        "error": ""
    })

@app.post("/usuarios_create")
def usuarios_create(request: Request, nombre: str = Form(...), correo: str = Form(...), password: str = Form(...), rol: str = Form(...)):
    usuario_sesion = request.session.get("usuario")
    if not usuario_sesion or usuario_sesion["rol"] != "admin":
        return RedirectResponse("/login", status_code=303)
    
    # VALIDACIONES
    error_msg = None
    
    # Validar nombre
    if not nombre or len(nombre) < 2 or len(nombre) > 50:
        error_msg = "El nombre debe tener entre 2 y 50 caracteres"
    elif not all(c.isalpha() or c.isspace() or c == '-' for c in nombre):
        error_msg = "El nombre solo debe contener letras, espacios y guiones"
    
    # Validar correo
    elif not correo or len(correo) < 5 or len(correo) > 50:
        error_msg = "El correo debe tener entre 5 y 50 caracteres"
    elif '@' not in correo or '.' not in correo:
        error_msg = "El correo debe tener un formato válido (ejemplo@correo.com)"
    
    # Validar password
    elif not password or len(password) < 6 or len(password) > 128:
        error_msg = "La contraseña debe tener entre 6 y 128 caracteres"
    
    # Validar rol
    elif rol not in ['admin', 'mecanico', 'conductor', 'logistica', 'observador']:
        error_msg = "El rol no es válido"
    
    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuario")
        usuarios = cursor.fetchall()
        db.close()
        return templates.TemplateResponse("usuarios.html", {
            "request": request, 
            "usuarios": usuarios, 
            "usuario": usuario_sesion,
            "buscar": "",
            "error": error_msg
        })
    
    db = get_db()
    cursor = db.cursor()
    
    # Validar que el correo no exista
    cursor.execute("SELECT * FROM usuario WHERE correo=%s", (correo,))
    if cursor.fetchone():
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM usuario")
        usuarios = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("usuarios.html", {
            "request": request, 
            "usuarios": usuarios, 
            "usuario": usuario_sesion,
            "buscar": "",
            "error": "El correo ya está registrado en el sistema"
        })
    
    try:
        cursor.execute("INSERT INTO usuario (nombre, correo, password, rol) VALUES (%s,%s,%s,%s)",
                       (nombre, correo, password, rol))
        db.commit()
        
        # Si es conductor, crear registro en tabla conductor
        if rol == "conductor":
            new_id = cursor.lastrowid
            parts = nombre.split(" ", 1)
            nombre_c = parts[0]
            apellido_c = parts[1] if len(parts) > 1 else ""
            cursor.execute("INSERT INTO conductor (nombre, apellido, telefono, direccion, fecha_nacimiento, id_usuario) VALUES (%s,%s,%s,%s,%s,%s)",
                           (nombre_c, apellido_c, None, None, None, new_id))
            db.commit()
        
        db.close()
        return RedirectResponse("/usuarios_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM usuario")
        usuarios = cursor2.fetchall()
        db2.close()
        return templates.TemplateResponse("usuarios.html", {
            "request": request, 
            "usuarios": usuarios, 
            "usuario": usuario_sesion,
            "buscar": "",
            "error": f"Error al crear usuario: {str(e)}"
        })

@app.get("/usuarios_edit/{id}")
def usuarios_edit(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/usuarios_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario WHERE id_usuario=%s", (id,))
    usuario_edit = cursor.fetchone()
    db.close()
    
    if not usuario_edit:
        return RedirectResponse("/usuarios_web", status_code=303)
    
    return templates.TemplateResponse("usuarios_edit.html", {
        "request": request, 
        "usuario_edit": usuario_edit, 
        "usuario": usuario,
        "error": ""
    })

@app.post("/usuarios_update/{id}")
def usuarios_update(request: Request, id: int, nombre: str = Form(...), correo: str = Form(...), password: str = Form(...), rol: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/usuarios_web", status_code=303)
    
    # VALIDACIONES
    error_msg = None
    
    # Validar nombre
    if not nombre or len(nombre) < 2 or len(nombre) > 50:
        error_msg = "El nombre debe tener entre 2 y 50 caracteres"
    elif not all(c.isalpha() or c.isspace() or c == '-' for c in nombre):
        error_msg = "El nombre solo debe contener letras, espacios y guiones"
    
    # Validar correo
    elif not correo or len(correo) < 5 or len(correo) > 50:
        error_msg = "El correo debe tener entre 5 y 50 caracteres"
    elif '@' not in correo or '.' not in correo:
        error_msg = "El correo debe tener un formato válido (ejemplo@correo.com)"
    
    # Validar password
    elif not password or len(password) < 6 or len(password) > 128:
        error_msg = "La contraseña debe tener entre 6 y 128 caracteres"
    
    # Validar rol
    elif rol not in ['admin', 'mecanico', 'conductor', 'logistica', 'observador']:
        error_msg = "El rol no es válido"
    
    if error_msg:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuario WHERE id_usuario=%s", (id,))
        usuario_edit = cursor.fetchone()
        db.close()
        return templates.TemplateResponse("usuarios_edit.html", {
            "request": request,
            "usuario_edit": usuario_edit,
            "usuario": usuario,
            "error": error_msg
        })
    
    db = get_db()
    cursor = db.cursor()
    
    # Validar que el correo no exista (excepto del usuario actual)
    cursor.execute("SELECT * FROM usuario WHERE correo=%s AND id_usuario!=%s", (correo, id))
    if cursor.fetchone():
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM usuario WHERE id_usuario=%s", (id,))
        usuario_edit = cursor2.fetchone()
        db2.close()
        return templates.TemplateResponse("usuarios_edit.html", {
            "request": request,
            "usuario_edit": usuario_edit,
            "usuario": usuario,
            "error": "El correo ya está registrado por otro usuario"
        })
    
    try:
        cursor.execute(
            "UPDATE usuario SET nombre=%s, correo=%s, password=%s, rol=%s WHERE id_usuario=%s",
            (nombre, correo, password, rol, id)
        )
        db.commit()
        db.close()
        return RedirectResponse("/usuarios_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM usuario WHERE id_usuario=%s", (id,))
        usuario_edit = cursor2.fetchone()
        db2.close()
        return templates.TemplateResponse("usuarios_edit.html", {
            "request": request,
            "usuario_edit": usuario_edit,
            "usuario": usuario,
            "error": f"Error al actualizar usuario: {str(e)}"
        })
    
@app.get("/usuarios_delete/{id}")
def usuarios_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/usuarios_web", status_code=303)
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM usuario WHERE id_usuario=%s", (id,))
        db.commit()
        db.close()
        return RedirectResponse("/usuarios_web", status_code=303)
    except Exception as e:
        db.close()
        return RedirectResponse("/usuarios_web", status_code=303)

# ==================== REPORTES ====================
# Nota: Se contó con asistencia de IA para estructurar la lógica de esta sección
# (cálculo de KPIs y preparación de datos de reportes), por combinar múltiples
# consultas, métricas y filtros de fecha de forma consistente.
@app.get("/reportes_web")
def reportes_web(request: Request, fecha_inicio: str = "", fecha_fin: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    
    # Obtener lista de conductores para el selector y calcular KPIs del rango
    db = get_db()
    cur_dict = db.cursor(dictionary=True)
    cur_dict.execute("SELECT id_conductor, nombre, apellido FROM conductor ORDER BY nombre, apellido")
    conductores = cur_dict.fetchall()

    cur = db.cursor()
    # Helper para escalar
    def escalar(q, params):
        cur.execute(q, params)
        r = cur.fetchone()
        return r[0] if r and r[0] is not None else 0

    rango = []
    where_viajes = ""
    where_fecha = ""
    if fecha_inicio:
        where_viajes += " AND fecha_salida >= %s"
        where_fecha += " AND fecha >= %s"
        rango.append(fecha_inicio)
    if fecha_fin:
        where_viajes += " AND fecha_salida <= %s"
        where_fecha += " AND fecha <= %s"
        rango.append(fecha_fin)

    # a) Viajes y cumplimiento
    total_viajes = escalar(f"SELECT COUNT(*) FROM viaje WHERE 1=1{where_viajes}", rango)
    viajes_completados = escalar(f"SELECT COUNT(*) FROM viaje WHERE estado='completado' {where_viajes}", rango)
    viajes_cancelados = escalar(f"SELECT COUNT(*) FROM viaje WHERE estado='cancelado' {where_viajes}", rango)
    viajes_en_progreso = escalar(f"SELECT COUNT(*) FROM viaje WHERE estado='en progreso' {where_viajes}", rango)
    tasa_cumplimiento = round((viajes_completados / total_viajes) * 100, 2) if total_viajes > 0 else 0.0

    # b) Combustible y costos
    litros_totales = escalar(f"SELECT IFNULL(SUM(litros),0) FROM consumo WHERE 1=1{where_fecha}", rango)
    costo_total_combustible = escalar(f"SELECT IFNULL(SUM(costo),0) FROM consumo WHERE 1=1{where_fecha}", rango)
    costo_promedio_viaje_combustible = round((costo_total_combustible / total_viajes), 2) if total_viajes > 0 else 0.0

    # c) Mantenimiento y salud de flota
    total_mantenimientos = escalar(f"SELECT COUNT(*) FROM mantenimiento WHERE 1=1{where_fecha}", rango)
    costo_total_mantenimiento = escalar(f"SELECT IFNULL(SUM(costo),0) FROM mantenimiento WHERE 1=1{where_fecha}", rango)
    vehiculos_mantenidos = escalar(f"SELECT COUNT(DISTINCT id_vehiculo) FROM mantenimiento WHERE 1=1{where_fecha}", rango)

    # d) Seguridad y desempeño
    total_incidentes = escalar(f"SELECT COUNT(*) FROM incidente WHERE 1=1{where_fecha}", rango)
    tasa_incidentes_por_100_viajes = round(((total_incidentes / total_viajes) * 100), 2) if total_viajes > 0 else 0.0
    promedio_evaluacion = escalar(f"SELECT IFNULL(AVG(puntuacion),0) FROM evaluacion WHERE 1=1{where_fecha}", rango)

    db.close()

    kpis = {
        "total_viajes": total_viajes,
        "viajes_completados": viajes_completados,
        "viajes_cancelados": viajes_cancelados,
        "viajes_en_progreso": viajes_en_progreso,
        "tasa_cumplimiento": tasa_cumplimiento,
        "litros_totales": litros_totales,
        "costo_total_combustible": round(costo_total_combustible, 2),
        "costo_promedio_viaje_combustible": costo_promedio_viaje_combustible,
        "total_mantenimientos": total_mantenimientos,
        "costo_total_mantenimiento": round(costo_total_mantenimiento, 2),
        "vehiculos_mantenidos": vehiculos_mantenidos,
        "total_incidentes": total_incidentes,
        "tasa_incidentes_por_100_viajes": tasa_incidentes_por_100_viajes,
        "promedio_evaluacion": round(float(promedio_evaluacion), 2) if promedio_evaluacion is not None else 0.0
    }
    
    return templates.TemplateResponse("reportes.html", {
        "request": request, 
        "usuario": usuario,
        "conductores": conductores,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "kpis": kpis
    })

@app.get("/descargar_vehiculos_csv")
def descargar_vehiculos_csv(request: Request, fecha_inicio: str = "", fecha_fin: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM vehiculo")
    vehiculos = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id_vehiculo', 'matricula', 'modelo', 'tipo', 'capacidad', 'marca', 'estado', 'kilometraje'])
    writer.writeheader()
    writer.writerows(vehiculos)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=vehiculos.csv"}
    )

@app.get("/descargar_conductores_csv")
def descargar_conductores_csv(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM conductor")
    conductores = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id_conductor', 'nombre', 'apellido', 'telefono', 'direccion', 'fecha_nacimiento'])
    writer.writeheader()
    writer.writerows(conductores)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=conductores.csv"}
 )

@app.get("/descargar_viajes_csv")
def descargar_viajes_csv(request: Request, fecha_inicio: str = "", fecha_fin: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM viaje WHERE 1=1"
    params = []
    
    if fecha_inicio:
        query += " AND fecha_salida >= %s"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND fecha_salida <= %s"
        params.append(fecha_fin)
    
    cursor.execute(query, params)
    viajes = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id_viaje', 'origen', 'destino', 'fecha_salida', 'fecha_estimada', 'estado', 'id_conductor'])
    writer.writeheader()
    writer.writerows(viajes)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=viajes.csv"}
    )

@app.get("/descargar_consumo_csv")
def descargar_consumo_csv(request: Request, fecha_inicio: str = "", fecha_fin: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM consumo WHERE 1=1"
    params = []
    
    if fecha_inicio:
        query += " AND fecha >= %s"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND fecha <= %s"
        params.append(fecha_fin)
    
    cursor.execute(query, params)
    consumo = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id_consumo', 'matricula', 'litros', 'fecha', 'tipo_combustible', 'costo'])
    writer.writeheader()
    writer.writerows(consumo)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=consumo.csv"}
    )

# ==================== REPORTES POR CONDUCTOR ====================
@app.get("/descargar_conductor_consumo_csv/{id_conductor}")
def descargar_conductor_consumo_csv(request: Request, id_conductor: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener información del conductor
    cursor.execute("SELECT nombre, apellido FROM conductor WHERE id_conductor=%s", (id_conductor,))
    conductor = cursor.fetchone()
    
    if not conductor:
        db.close()
        return RedirectResponse("/reportes_web", status_code=303)
    
    # Obtener consumo de vehículos asociados al conductor mediante viajes
    cursor.execute("""
        SELECT DISTINCT c.id_consumo, c.matricula, c.litros, c.fecha, c.tipo_combustible, c.costo
        FROM consumo c
        JOIN vehiculo v ON c.matricula = v.matricula
        JOIN viaje vi ON vi.id_conductor = %s
        WHERE v.id_vehiculo IN (
            SELECT DISTINCT fv.id_vehiculo
            FROM flota_vehiculo fv
            JOIN flota f ON fv.id_flota = f.id_flota
            JOIN viaje v2 ON v2.id_conductor = %s
        )
        OR c.matricula IN (
            SELECT DISTINCT v3.matricula
            FROM vehiculo v3
            JOIN viaje v4 ON v4.id_conductor = %s
        )
        ORDER BY c.fecha DESC
    """, (id_conductor, id_conductor, id_conductor))
    consumo = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id_consumo', 'matricula', 'litros', 'fecha', 'tipo_combustible', 'costo'])
    writer.writeheader()
    writer.writerows(consumo)
    
    nombre_archivo = f"consumo_conductor_{conductor['nombre']}_{conductor['apellido']}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
    )

@app.get("/descargar_conductor_viajes_csv/{id_conductor}")
def descargar_conductor_viajes_csv(request: Request, id_conductor: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener información del conductor
    cursor.execute("SELECT nombre, apellido FROM conductor WHERE id_conductor=%s", (id_conductor,))
    conductor = cursor.fetchone()
    
    if not conductor:
        db.close()
        return RedirectResponse("/reportes_web", status_code=303)
    
    # Obtener viajes del conductor
    cursor.execute("""
        SELECT v.id_viaje, v.origen, v.destino, v.fecha_salida, v.fecha_estimada, v.estado, v.id_conductor
        FROM viaje v
        WHERE v.id_conductor = %s
        ORDER BY v.fecha_salida DESC
    """, (id_conductor,))
    viajes = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id_viaje', 'origen', 'destino', 'fecha_salida', 'fecha_estimada', 'estado', 'id_conductor'])
    writer.writeheader()
    writer.writerows(viajes)
    
    nombre_archivo = f"viajes_conductor_{conductor['nombre']}_{conductor['apellido']}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
    )

@app.get("/descargar_conductor_vehiculos_csv/{id_conductor}")
def descargar_conductor_vehiculos_csv(request: Request, id_conductor: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener información del conductor
    cursor.execute("SELECT nombre, apellido FROM conductor WHERE id_conductor=%s", (id_conductor,))
    conductor = cursor.fetchone()
    
    if not conductor:
        db.close()
        return RedirectResponse("/reportes_web", status_code=303)
    
    # Obtener vehículos utilizados por el conductor en viajes
    cursor.execute("""
        SELECT DISTINCT v.id_vehiculo, v.matricula, v.modelo, v.tipo, v.capacidad, v.marca, v.estado, v.kilometraje
        FROM vehiculo v
        JOIN flota_vehiculo fv ON v.id_vehiculo = fv.id_vehiculo
        JOIN flota f ON fv.id_flota = f.id_flota
        WHERE EXISTS (
            SELECT 1 FROM viaje vi WHERE vi.id_conductor = %s
        )
        ORDER BY v.matricula
    """, (id_conductor,))
    vehiculos = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id_vehiculo', 'matricula', 'modelo', 'tipo', 'capacidad', 'marca', 'estado', 'kilometraje'])
    writer.writeheader()
    writer.writerows(vehiculos)
    
    nombre_archivo = f"vehiculos_conductor_{conductor['nombre']}_{conductor['apellido']}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
    )

@app.get("/descargar_conductor_mantenimiento_csv/{id_conductor}")
def descargar_conductor_mantenimiento_csv(request: Request, id_conductor: int, fecha_inicio: str = "", fecha_fin: str = ""):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT nombre, apellido FROM conductor WHERE id_conductor=%s", (id_conductor,))
    conductor = cursor.fetchone()
    
    if not conductor:
        db.close()
        return RedirectResponse("/reportes_web", status_code=303)
    
    query = """
        SELECT DISTINCT m.id_mantenimiento, m.id_vehiculo, m.tipo, m.descripcion, m.costo, m.fecha,
               v.matricula
        FROM mantenimiento m
        JOIN vehiculo v ON m.id_vehiculo = v.id_vehiculo
        JOIN flota_vehiculo fv ON v.id_vehiculo = fv.id_vehiculo
        WHERE EXISTS (
            SELECT 1 FROM viaje vi WHERE vi.id_conductor = %s
        )
    """
    params = [id_conductor]
    
    if fecha_inicio:
        query += " AND m.fecha >= %s"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND m.fecha <= %s"
        params.append(fecha_fin)
    
    query += " ORDER BY m.fecha DESC"
    cursor.execute(query, params)
    mantenimiento = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id_mantenimiento', 'id_vehiculo', 'matricula', 'tipo', 'descripcion', 'costo', 'fecha'])
    writer.writeheader()
    writer.writerows(mantenimiento)
    
    nombre_archivo = f"mantenimiento_conductor_{conductor['nombre']}_{conductor['apellido']}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
    )

@app.get("/descargar_conductor_incidentes_csv/{id_conductor}")
def descargar_conductor_incidentes_csv(request: Request, id_conductor: int, fecha_inicio: str = "", fecha_fin: str = ""):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT nombre, apellido FROM conductor WHERE id_conductor=%s", (id_conductor,))
    conductor = cursor.fetchone()
    
    if not conductor:
        db.close()
        return RedirectResponse("/reportes_web", status_code=303)
    
    query = """
        SELECT DISTINCT i.id_incidente, i.matricula, i.tipo, i.fecha, i.descripcion
        FROM incidente i
        JOIN vehiculo v ON i.matricula = v.matricula
        WHERE EXISTS (
            SELECT 1 FROM viaje vi WHERE vi.id_conductor = %s
        )
    """
    params = [id_conductor]
    
    if fecha_inicio:
        query += " AND i.fecha >= %s"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND i.fecha <= %s"
        params.append(fecha_fin)
    
    query += " ORDER BY i.fecha DESC"
    cursor.execute(query, params)
    incidentes = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id_incidente', 'matricula', 'tipo', 'fecha', 'descripcion'])
    writer.writeheader()
    writer.writerows(incidentes)
    
    nombre_archivo = f"incidentes_conductor_{conductor['nombre']}_{conductor['apellido']}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
    )

@app.get("/descargar_conductor_evaluaciones_csv/{id_conductor}")
def descargar_conductor_evaluaciones_csv(request: Request, id_conductor: int, fecha_inicio: str = "", fecha_fin: str = ""):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT nombre, apellido FROM conductor WHERE id_conductor=%s", (id_conductor,))
    conductor = cursor.fetchone()
    
    if not conductor:
        db.close()
        return RedirectResponse("/reportes_web", status_code=303)
    
    query = """
        SELECT e.id_evaluacion, e.id_conductor, e.fecha, e.puntuacion, e.comentarios
        FROM evaluacion e
        WHERE e.id_conductor = %s
    """
    params = [id_conductor]
    
    if fecha_inicio:
        query += " AND e.fecha >= %s"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND e.fecha <= %s"
        params.append(fecha_fin)
    
    query += " ORDER BY e.fecha DESC"
    cursor.execute(query, params)
    evaluaciones = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id_evaluacion', 'id_conductor', 'fecha', 'puntuacion', 'comentarios'])
    writer.writeheader()
    writer.writerows(evaluaciones)
    
    nombre_archivo = f"evaluaciones_conductor_{conductor['nombre']}_{conductor['apellido']}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
    )

@app.get("/descargar_conductor_licencias_csv/{id_conductor}")
def descargar_conductor_licencias_csv(request: Request, id_conductor: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT nombre, apellido FROM conductor WHERE id_conductor=%s", (id_conductor,))
    conductor = cursor.fetchone()
    
    if not conductor:
        db.close()
        return RedirectResponse("/reportes_web", status_code=303)
    
    cursor.execute("""
        SELECT l.id_licencia, l.id_conductor, l.tipo, l.fecha_emision, l.fecha_vencimiento
        FROM licencia l
        WHERE l.id_conductor = %s
        ORDER BY l.fecha_emision DESC
    """, (id_conductor,))
    licencias = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id_licencia', 'id_conductor', 'tipo', 'fecha_emision', 'fecha_vencimiento'])
    writer.writeheader()
    writer.writerows(licencias)
    
    nombre_archivo = f"licencias_conductor_{conductor['nombre']}_{conductor['apellido']}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
    )

# Nota: Se utilizó asistencia de IA para diseñar la agregación multi-tabla y
# el formateo del CSV consolidado en este endpoint.
@app.get("/descargar_reporte_general_csv")
def descargar_reporte_general_csv(request: Request, fecha_inicio: str = "", fecha_fin: str = ""):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    output = io.StringIO()
    
    # VEHÍCULOS
    output.write("=== VEHÍCULOS ===\n")
    cursor.execute("SELECT * FROM vehiculo")
    vehiculos = cursor.fetchall()
    if vehiculos:
        writer = csv.DictWriter(output, fieldnames=['id_vehiculo', 'matricula', 'modelo', 'tipo', 'capacidad', 'marca', 'estado', 'kilometraje'])
        writer.writeheader()
        writer.writerows(vehiculos)
    output.write("\n")
    
    # CONDUCTORES
    output.write("=== CONDUCTORES ===\n")
    cursor.execute("SELECT * FROM conductor")
    conductores = cursor.fetchall()
    if conductores:
        writer = csv.DictWriter(output, fieldnames=['id_conductor', 'nombre', 'apellido', 'telefono', 'direccion', 'fecha_nacimiento', 'id_usuario'])
        writer.writeheader()
        writer.writerows(conductores)
    output.write("\n")
    
    # VIAJES
    output.write("=== VIAJES ===\n")
    query = "SELECT * FROM viaje WHERE 1=1"
    params = []
    if fecha_inicio:
        query += " AND fecha_salida >= %s"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND fecha_salida <= %s"
        params.append(fecha_fin)
    cursor.execute(query, params)
    viajes = cursor.fetchall()
    if viajes:
        writer = csv.DictWriter(output, fieldnames=['id_viaje', 'origen', 'destino', 'fecha_salida', 'fecha_estimada', 'estado', 'id_conductor'])
        writer.writeheader()
        writer.writerows(viajes)
    output.write("\n")
    
    # CONSUMO
    output.write("=== CONSUMO ===\n")
    query = "SELECT * FROM consumo WHERE 1=1"
    params = []
    if fecha_inicio:
        query += " AND fecha >= %s"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND fecha <= %s"
        params.append(fecha_fin)
    cursor.execute(query, params)
    consumo = cursor.fetchall()
    if consumo:
        writer = csv.DictWriter(output, fieldnames=['id_consumo', 'matricula', 'litros', 'fecha', 'tipo_combustible', 'costo'])
        writer.writeheader()
        writer.writerows(consumo)
    output.write("\n")
    
    # MANTENIMIENTO
    output.write("=== MANTENIMIENTO ===\n")
    query = "SELECT * FROM mantenimiento WHERE 1=1"
    params = []
    if fecha_inicio:
        query += " AND fecha >= %s"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND fecha <= %s"
        params.append(fecha_fin)
    cursor.execute(query, params)
    mantenimiento = cursor.fetchall()
    if mantenimiento:
        writer = csv.DictWriter(output, fieldnames=['id_mantenimiento', 'id_vehiculo', 'tipo', 'descripcion', 'costo', 'fecha'])
        writer.writeheader()
        writer.writerows(mantenimiento)
    output.write("\n")
    
    # INCIDENTES
    output.write("=== INCIDENTES ===\n")
    query = "SELECT * FROM incidente WHERE 1=1"
    params = []
    if fecha_inicio:
        query += " AND fecha >= %s"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND fecha <= %s"
        params.append(fecha_fin)
    cursor.execute(query, params)
    incidentes = cursor.fetchall()
    if incidentes:
        writer = csv.DictWriter(output, fieldnames=['id_incidente', 'matricula', 'tipo', 'fecha', 'descripcion'])
        writer.writeheader()
        writer.writerows(incidentes)
    output.write("\n")
    
    # EVALUACIONES
    output.write("=== EVALUACIONES ===\n")
    query = "SELECT * FROM evaluacion WHERE 1=1"
    params = []
    if fecha_inicio:
        query += " AND fecha >= %s"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND fecha <= %s"
        params.append(fecha_fin)
    cursor.execute(query, params)
    evaluaciones = cursor.fetchall()
    if evaluaciones:
        writer = csv.DictWriter(output, fieldnames=['id_evaluacion', 'id_conductor', 'fecha', 'puntuacion', 'comentarios'])
        writer.writeheader()
        writer.writerows(evaluaciones)
    output.write("\n")
    
    # LICENCIAS
    output.write("=== LICENCIAS ===\n")
    cursor.execute("SELECT * FROM licencia")
    licencias = cursor.fetchall()
    if licencias:
        writer = csv.DictWriter(output, fieldnames=['id_licencia', 'id_conductor', 'tipo', 'fecha_emision', 'fecha_vencimiento'])
        writer.writeheader()
        writer.writerows(licencias)
    output.write("\n")
    
    # ORDENES
    output.write("=== ORDENES DE SERVICIO ===\n")
    query = "SELECT * FROM orden_servicio WHERE 1=1"
    params = []
    if fecha_inicio:
        query += " AND fecha >= %s"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND fecha <= %s"
        params.append(fecha_fin)
    cursor.execute(query, params)
    ordenes = cursor.fetchall()
    if ordenes:
        writer = csv.DictWriter(output, fieldnames=['id_orden', 'descripcion', 'fecha', 'estado'])
        writer.writeheader()
        writer.writerows(ordenes)
    
    db.close()
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reporte_general_completo.csv"}
    )

# ==================== REPORTES AVANZADOS (ANÁLISIS CRUZADO) ====================

# Nota: Se contó con asistencia de IA para el armado de la consulta cruzada
# y el cálculo de promedios/agrupaciones de este reporte avanzado.
@app.get("/descargar_reporte_consumo_combustible_csv")
def descargar_reporte_consumo_combustible_csv(request: Request, fecha_inicio: str = "", fecha_fin: str = ""):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/reportes_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = """
        SELECT 
            f.nombre AS flota,
            v.matricula,
            v.modelo,
            v.marca,
            SUM(c.litros) AS litros_totales,
            SUM(c.costo) AS costo_total,
            ROUND(SUM(c.costo) / NULLIF(SUM(c.litros),0), 2) AS costo_promedio_litro
        FROM consumo c
        JOIN vehiculo v ON c.matricula = v.matricula
        LEFT JOIN flota f ON v.id_flota = f.id_flota
        WHERE 1=1
    """
    
    params = []
    if fecha_inicio:
        query += " AND c.fecha >= %s"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND c.fecha <= %s"
        params.append(fecha_fin)
    
    query += " GROUP BY f.nombre, v.matricula, v.modelo, v.marca ORDER BY f.nombre, v.matricula"
    
    cursor.execute(query, params)
    resultados = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['flota', 'matricula', 'modelo', 'marca', 'litros_totales', 'costo_total', 'costo_promedio_litro'])
    writer.writeheader()
    writer.writerows(resultados)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reporte_consumo_combustible.csv"}
    )

# Nota: Se utilizó asistencia de IA para componer subconsultas y combinarlas
# en un reporte que suma costos de combustible y mantenimiento por vehículo.
@app.get("/descargar_reporte_costos_operativos_csv")
def descargar_reporte_costos_operativos_csv(request: Request, fecha_inicio: str = "", fecha_fin: str = ""):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/reportes_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Subconsulta para combustible
    query_combustible = """
        SELECT 
            matricula,
            SUM(costo) AS costo_combustible
        FROM consumo
        WHERE 1=1
    """
    params_comb = []
    if fecha_inicio:
        query_combustible += " AND fecha >= %s"
        params_comb.append(fecha_inicio)
    if fecha_fin:
        query_combustible += " AND fecha <= %s"
        params_comb.append(fecha_fin)
    query_combustible += " GROUP BY matricula"
    
    # Subconsulta para mantenimiento
    query_mant = """
        SELECT 
            id_vehiculo,
            SUM(costo) AS costo_mantenimiento
        FROM mantenimiento
        WHERE 1=1
    """
    params_mant = []
    if fecha_inicio:
        query_mant += " AND fecha >= %s"
        params_mant.append(fecha_inicio)
    if fecha_fin:
        query_mant += " AND fecha <= %s"
        params_mant.append(fecha_fin)
    query_mant += " GROUP BY id_vehiculo"
    
    # Query principal
    query = f"""
        SELECT
            f.nombre AS flota,
            v.matricula,
            v.modelo,
            v.marca,
            IFNULL(cons.costo_combustible, 0) AS costo_combustible,
            IFNULL(mant.costo_mantenimiento, 0) AS costo_mantenimiento,
            IFNULL(cons.costo_combustible, 0) + IFNULL(mant.costo_mantenimiento, 0) AS costo_total
        FROM vehiculo v
        LEFT JOIN flota f ON v.id_flota = f.id_flota
        LEFT JOIN ({query_combustible}) cons ON cons.matricula = v.matricula
        LEFT JOIN ({query_mant}) mant ON mant.id_vehiculo = v.id_vehiculo
        ORDER BY f.nombre, v.matricula
    """
    
    cursor.execute(query, params_comb + params_mant)
    resultados = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['flota', 'matricula', 'modelo', 'marca', 'costo_combustible', 'costo_mantenimiento', 'costo_total'])
    writer.writeheader()
    writer.writerows(resultados)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reporte_costos_operativos.csv"}
    )

# Nota: Asistencia de IA para integrar viajes, evaluaciones e incidentes en
# un único reporte con métricas por conductor.
@app.get("/descargar_reporte_desempeno_conductores_csv")
def descargar_reporte_desempeno_conductores_csv(request: Request, fecha_inicio: str = "", fecha_fin: str = ""):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/reportes_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = """
        SELECT
            c.id_conductor,
            CONCAT(c.nombre, ' ', c.apellido) AS conductor,
            COUNT(DISTINCT vj.id_viaje) AS total_viajes,
            ROUND(AVG(ev.puntuacion), 2) AS promedio_evaluacion,
            COUNT(DISTINCT inc.id_incidente) AS incidentes_asociados
        FROM conductor c
        LEFT JOIN viaje vj ON vj.id_conductor = c.id_conductor
        LEFT JOIN evaluacion ev ON ev.id_conductor = c.id_conductor
        LEFT JOIN vehiculo ve ON vj.id_vehiculo = ve.id_vehiculo
        LEFT JOIN incidente inc ON inc.matricula = ve.matricula
        WHERE 1=1
    """
    
    params = []
    if fecha_inicio:
        query += " AND vj.fecha_salida >= %s"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND vj.fecha_salida <= %s"
        params.append(fecha_fin)
    
    query += " GROUP BY c.id_conductor, conductor ORDER BY total_viajes DESC"
    
    cursor.execute(query, params)
    resultados = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id_conductor', 'conductor', 'total_viajes', 'promedio_evaluacion', 'incidentes_asociados'])
    writer.writeheader()
    writer.writerows(resultados)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reporte_desempeno_conductores.csv"}
    )

# Nota: Asistencia de IA para determinar estados de licencia y cruzarlos con
# viajes en rango, generando métricas de cumplimiento.
@app.get("/descargar_reporte_licencias_cumplimiento_csv")
def descargar_reporte_licencias_cumplimiento_csv(request: Request, fecha_inicio: str = "", fecha_fin: str = ""):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/reportes_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = """
        SELECT
            c.id_conductor,
            CONCAT(c.nombre, ' ', c.apellido) AS conductor,
            l.tipo,
            l.fecha_emision,
            l.fecha_vencimiento,
            CASE
                WHEN l.fecha_vencimiento < CURDATE() THEN 'VENCIDA'
                WHEN l.fecha_vencimiento BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                    THEN 'POR VENCER'
                ELSE 'VIGENTE'
            END AS estado_licencia,
            COUNT(DISTINCT vj.id_viaje) AS viajes_en_rango
        FROM licencia l
        JOIN conductor c ON c.id_conductor = l.id_conductor
        LEFT JOIN viaje vj ON vj.id_conductor = c.id_conductor
    """
    
    params = []
    where_conditions = []
    
    if fecha_inicio:
        where_conditions.append("vj.fecha_salida >= %s")
        params.append(fecha_inicio)
    if fecha_fin:
        where_conditions.append("vj.fecha_salida <= %s")
        params.append(fecha_fin)
    
    if where_conditions:
        query += " AND " + " AND ".join(where_conditions)
    
    query += " GROUP BY c.id_conductor, conductor, l.tipo, l.fecha_emision, l.fecha_vencimiento ORDER BY estado_licencia DESC, viajes_en_rango DESC"
    
    cursor.execute(query, params)
    resultados = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id_conductor', 'conductor', 'tipo', 'fecha_emision', 'fecha_vencimiento', 'estado_licencia', 'viajes_en_rango'])
    writer.writeheader()
    writer.writerows(resultados)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reporte_licencias_cumplimiento.csv"}
    )

# Nota: Se contó con asistencia de IA para estandarizar el cálculo de KPIs y
# su exportación a CSV con columnas normalizadas.
@app.get("/descargar_reporte_kpis_csv")
def descargar_reporte_kpis_csv(request: Request, fecha_inicio: str = "", fecha_fin: str = ""):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/reportes_web", status_code=303)

    db = get_db()
    cursor = db.cursor()

    # Utilidad para ejecutar escalar con rango
    def escalar(query_base, params):
        cursor.execute(query_base, params)
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else 0

    rango = []
    where_viajes = ""
    where_fecha = ""
    if fecha_inicio:
        where_viajes += " AND fecha_salida >= %s"
        where_fecha += " AND fecha >= %s"
        rango.append(fecha_inicio)
    if fecha_fin:
        where_viajes += " AND fecha_salida <= %s"
        where_fecha += " AND fecha <= %s"
        rango.append(fecha_fin)

    # a) Viajes y cumplimiento
    total_viajes = escalar(f"SELECT COUNT(*) FROM viaje WHERE 1=1{where_viajes}", rango)
    viajes_completados = escalar(f"SELECT COUNT(*) FROM viaje WHERE estado='completado' {where_viajes}", rango)
    viajes_cancelados = escalar(f"SELECT COUNT(*) FROM viaje WHERE estado='cancelado' {where_viajes}", rango)
    viajes_en_progreso = escalar(f"SELECT COUNT(*) FROM viaje WHERE estado='en progreso' {where_viajes}", rango)
    tasa_cumplimiento = round((viajes_completados / total_viajes) * 100, 2) if total_viajes > 0 else 0.0

    # b) Combustible y costos
    litros_totales = escalar(f"SELECT IFNULL(SUM(litros),0) FROM consumo WHERE 1=1{where_fecha}", rango)
    costo_total_combustible = escalar(f"SELECT IFNULL(SUM(costo),0) FROM consumo WHERE 1=1{where_fecha}", rango)
    costo_promedio_viaje_combustible = round((costo_total_combustible / total_viajes), 2) if total_viajes > 0 else 0.0

    # c) Mantenimiento y salud de flota
    total_mantenimientos = escalar(f"SELECT COUNT(*) FROM mantenimiento WHERE 1=1{where_fecha}", rango)
    costo_total_mantenimiento = escalar(f"SELECT IFNULL(SUM(costo),0) FROM mantenimiento WHERE 1=1{where_fecha}", rango)
    vehiculos_mantenidos = escalar(f"SELECT COUNT(DISTINCT id_vehiculo) FROM mantenimiento WHERE 1=1{where_fecha}", rango)

    # d) Seguridad y desempeño
    total_incidentes = escalar(f"SELECT COUNT(*) FROM incidente WHERE 1=1{where_fecha}", rango)
    tasa_incidentes_por_100_viajes = round(((total_incidentes / total_viajes) * 100), 2) if total_viajes > 0 else 0.0
    promedio_evaluacion = escalar(f"SELECT IFNULL(AVG(puntuacion),0) FROM evaluacion WHERE 1=1{where_fecha}", rango)

    db.close()

    # CSV de una sola fila con columnas de KPIs
    output = io.StringIO()
    fieldnames = [
        'total_viajes', 'viajes_completados', 'viajes_cancelados', 'viajes_en_progreso', 'tasa_cumplimiento',
        'litros_totales', 'costo_total_combustible', 'costo_promedio_viaje_combustible',
        'total_mantenimientos', 'costo_total_mantenimiento', 'vehiculos_mantenidos',
        'total_incidentes', 'tasa_incidentes_por_100_viajes', 'promedio_evaluacion'
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow({
        'total_viajes': total_viajes,
        'viajes_completados': viajes_completados,
        'viajes_cancelados': viajes_cancelados,
        'viajes_en_progreso': viajes_en_progreso,
        'tasa_cumplimiento': tasa_cumplimiento,
        'litros_totales': litros_totales,
        'costo_total_combustible': round(costo_total_combustible, 2),
        'costo_promedio_viaje_combustible': costo_promedio_viaje_combustible,
        'total_mantenimientos': total_mantenimientos,
        'costo_total_mantenimiento': round(costo_total_mantenimiento, 2),
        'vehiculos_mantenidos': vehiculos_mantenidos,
        'total_incidentes': total_incidentes,
        'tasa_incidentes_por_100_viajes': tasa_incidentes_por_100_viajes,
        'promedio_evaluacion': round(float(promedio_evaluacion), 2) if promedio_evaluacion is not None else 0.0
    })

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reporte_kpis.csv"}
    )