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

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecret")

templates = Jinja2Templates(directory="templates")

def get_db():
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
    cursor.execute("SELECT * FROM usuario WHERE correo=%s AND password=%s", (correo, password))
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

# ==================== VEHICULOS ====================
@app.get("/vehiculos_web")
def vehiculos_web(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM vehiculo")
    vehiculos = cursor.fetchall()
    db.close()
    return templates.TemplateResponse("vehiculos.html", {"request": request, "vehiculos": vehiculos, "usuario": usuario})

@app.post("/vehiculos_create")
def vehiculos_create(request: Request, matricula: str = Form(...), modelo: str = Form(...), tipo: str = Form(...), capacidad: int = Form(...), marca: str = Form(...), estado: str = Form(...), kilometraje: int = Form(...)):
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
            "INSERT INTO vehiculo (matricula, modelo, tipo, capacidad, marca, estado, kilometraje) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (matricula, modelo, tipo, capacidad, marca, estado, kilometraje)
        )
        db.commit()
        db.close()
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
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM vehiculo WHERE id_vehiculo=%s", (id,))
        db.commit()
        db.close()
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
    if not usuario or usuario["rol"] != "admin":
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
def vehiculos_update(request: Request, id: int, matricula: str = Form(...), modelo: str = Form(...), tipo: str = Form(...), capacidad: int = Form(...), marca: str = Form(...), estado: str = Form(...), kilometraje: int = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
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
            "UPDATE vehiculo SET matricula=%s, modelo=%s, tipo=%s, capacidad=%s, marca=%s, estado=%s, kilometraje=%s WHERE id_vehiculo=%s",
            (matricula, modelo, tipo, capacidad, marca, estado, kilometraje, id)
        )
        db.commit()
        db.close()
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
def conductores_web(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM conductor")
    conductores = cursor.fetchall()
    db.close()
    return templates.TemplateResponse("conductores.html", {"request": request, "conductores": conductores, "usuario": usuario})

@app.post("/conductores_create")
def conductores_create(request: Request, nombre: str = Form(...), apellido: str = Form(...), telefono: str = Form(...), direccion: str = Form(...), fecha_nacimiento: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/conductores_web", status_code=303)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO conductor (nombre, apellido, telefono, direccion, fecha_nacimiento) VALUES (%s,%s,%s,%s,%s)",
                   (nombre, apellido, telefono, direccion, fecha_nacimiento))
    db.commit()
    db.close()
    return RedirectResponse("/conductores_web", status_code=303)

@app.get("/conductores_delete/{id}")
def conductores_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/conductores_web", status_code=303)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM conductor WHERE id_conductor=%s", (id,))
    db.commit()
    db.close()
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
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE conductor SET nombre=%s, apellido=%s, telefono=%s, direccion=%s, fecha_nacimiento=%s WHERE id_conductor=%s",
            (nombre, apellido, telefono, direccion, fecha_nacimiento, id)
        )
        db.commit()
        db.close()
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
def viajes_web(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM viaje")
    viajes = cursor.fetchall()
    db.close()
    return templates.TemplateResponse("viajes.html", {"request": request, "viajes": viajes, "usuario": usuario})

@app.post("/viajes_create")
def viajes_create(request: Request, origen: str = Form(...), destino: str = Form(...), fecha_salida: str = Form(...), estado: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] not in ["admin", "logistica"]:
        return RedirectResponse("/viajes_web", status_code=303)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO viaje (origen, destino, fecha_salida, estado) VALUES (%s,%s,%s,%s)",
                   (origen, destino, fecha_salida, estado))
    db.commit()
    db.close()
    return RedirectResponse("/viajes_web", status_code=303)

@app.get("/viajes_delete/{id}")
def viajes_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/viajes_web", status_code=303)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM viaje WHERE id_viaje=%s", (id,))
    db.commit()
    db.close()
    return RedirectResponse("/viajes_web", status_code=303)

@app.get("/viajes_edit/{id}")
def viajes_edit(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/viajes_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM viaje WHERE id_viaje=%s", (id,))
    viaje = cursor.fetchone()
    db.close()
    
    if not viaje:
        return RedirectResponse("/viajes_web", status_code=303)
    
    return templates.TemplateResponse("viajes_edit.html", {"request": request, "viaje": viaje, "usuario": usuario})

@app.post("/viajes_update/{id}")
def viajes_update(request: Request, id: int, origen: str = Form(...), destino: str = Form(...), fecha_salida: str = Form(...), estado: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/viajes_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE viaje SET origen=%s, destino=%s, fecha_salida=%s, estado=%s WHERE id_viaje=%s",
            (origen, destino, fecha_salida, estado, id)
        )
        db.commit()
        db.close()
        return RedirectResponse("/viajes_web", status_code=303)
    except Exception as e:
        db.close()
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM viaje WHERE id_viaje=%s", (id,))
        viaje = cursor2.fetchone()
        db2.close()
        return templates.TemplateResponse("viajes_edit.html", {
            "request": request,
            "viaje": viaje,
            "usuario": usuario,
            "error": "Error al actualizar viaje"
        })

# ==================== MANTENIMIENTO ====================
@app.get("/mantenimiento_web")
def mantenimiento_web(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM mantenimiento")
    mant = cursor.fetchall()
    db.close()
    return templates.TemplateResponse("mantenimiento.html", {"request": request, "mantenimiento": mant, "usuario": usuario})

@app.post("/mantenimiento_create")
def mantenimiento_create(request: Request, id_vehiculo: int = Form(...), descripcion: str = Form(...), fecha: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "mecanico":
        return RedirectResponse("/mantenimiento_web", status_code=303)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO mantenimiento (id_vehiculo, descripcion, fecha) VALUES (%s,%s,%s)",
                   (id_vehiculo, descripcion, fecha))
    db.commit()
    db.close()
    return RedirectResponse("/mantenimiento_web", status_code=303)

@app.get("/mantenimiento_delete/{id}")
def mantenimiento_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "mecanico":
        return RedirectResponse("/mantenimiento_web", status_code=303)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM mantenimiento WHERE id_mantenimiento=%s", (id,))
    db.commit()
    db.close()
    return RedirectResponse("/mantenimiento_web", status_code=303)

# ==================== CONSUMO ====================
@app.get("/consumo_web")
def consumo_web(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM consumo")
    cons = cursor.fetchall()
    db.close()
    return templates.TemplateResponse("consumo.html", {"request": request, "consumo": cons, "usuario": usuario})

@app.post("/consumo_create")
def consumo_create(request: Request, id_vehiculo: int = Form(...), litros: float = Form(...), fecha: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "mecanico":
        return RedirectResponse("/consumo_web", status_code=303)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO consumo (id_vehiculo, litros, fecha) VALUES (%s,%s,%s)",
                   (id_vehiculo, litros, fecha))
    db.commit()
    db.close()
    return RedirectResponse("/consumo_web", status_code=303)

@app.get("/consumo_delete/{id}")
def consumo_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "mecanico":
        return RedirectResponse("/consumo_web", status_code=303)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM consumo WHERE id_consumo=%s", (id,))
    db.commit()
    db.close()
    return RedirectResponse("/consumo_web", status_code=303)

# ==================== FLOTA ====================
@app.get("/flota_web")
def flota_web(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM flota")
    flotas = cursor.fetchall()
    db.close()
    return templates.TemplateResponse("flota.html", {"request": request, "flota": flotas, "usuario": usuario})

@app.post("/flota_create")
def flota_create(request: Request, nombre: str = Form(...), descripcion: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/flota_web", status_code=303)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO flota (nombre, descripcion) VALUES (%s,%s)",
                   (nombre, descripcion))
    db.commit()
    db.close()
    return RedirectResponse("/flota_web", status_code=303)

@app.get("/flota_delete/{id}")
def flota_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/flota_web", status_code=303)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM flota WHERE id_flota=%s", (id,))
    db.commit()
    db.close()
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
def flota_update(request: Request, id: int, nombre: str = Form(...), descripcion: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/flota_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE flota SET nombre=%s, descripcion=%s WHERE id_flota=%s",
            (nombre, descripcion, id)
        )
        db.commit()
        db.close()
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
def incidentes_web(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM incidente")
    inc = cursor.fetchall()
    db.close()
    return templates.TemplateResponse("incidentes.html", {"request": request, "incidentes": inc, "usuario": usuario})

@app.post("/incidentes_create")
def incidentes_create(request: Request, id_vehiculo: int = Form(...), tipo: str = Form(...), fecha: str = Form(...), descripcion: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "mecanico":
        return RedirectResponse("/incidentes_web", status_code=303)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO incidente (id_vehiculo, tipo, fecha, descripcion) VALUES (%s,%s,%s,%s)",
                   (id_vehiculo, tipo, fecha, descripcion))
    db.commit()
    db.close()
    return RedirectResponse("/incidentes_web", status_code=303)

@app.get("/incidentes_delete/{id}")
def incidentes_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "mecanico":
        return RedirectResponse("/incidentes_web", status_code=303)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM incidente WHERE id_incidente=%s", (id,))
    db.commit()
    db.close()
    return RedirectResponse("/incidentes_web", status_code=303)

# ==================== ORDENES ====================
@app.get("/ordenes_web")
def ordenes_web(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orden_servicio")
    ordenes = cursor.fetchall()
    db.close()
    return templates.TemplateResponse("ordenes.html", {"request": request, "ordenes": ordenes, "usuario": usuario})

@app.post("/ordenes_create")
def ordenes_create(request: Request, descripcion: str = Form(...), fecha: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] not in ["admin", "logistica"]:
        return RedirectResponse("/ordenes_web", status_code=303)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO orden_servicio (descripcion, fecha) VALUES (%s,%s)",
                   (descripcion, fecha))
    db.commit()
    db.close()
    return RedirectResponse("/ordenes_web", status_code=303)

@app.get("/ordenes_delete/{id}")
def ordenes_delete(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/ordenes_web", status_code=303)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM orden_servicio WHERE id_orden=%s", (id,))
    db.commit()
    db.close()
    return RedirectResponse("/ordenes_web", status_code=303)

@app.get("/ordenes_edit/{id}")
def ordenes_edit(request: Request, id: int):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/ordenes_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orden_servicio WHERE id_orden=%s", (id,))
    orden = cursor.fetchone()
    db.close()
    
    if not orden:
        return RedirectResponse("/ordenes_web", status_code=303)
    
    return templates.TemplateResponse("ordenes_edit.html", {"request": request, "orden": orden, "usuario": usuario})

@app.post("/ordenes_update/{id}")
def ordenes_update(request: Request, id: int, descripcion: str = Form(...), fecha: str = Form(...)):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/ordenes_web", status_code=303)
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE orden_servicio SET descripcion=%s, fecha=%s WHERE id_orden=%s",
            (descripcion, fecha, id)
        )
        db.commit()
        db.close()
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
            "error": "Error al actualizar orden"
        })

# ==================== USUARIOS ====================
@app.get("/usuarios_web")
def usuarios_web(request: Request):
    usuario = request.session.get("usuario")
    if not usuario or usuario["rol"] != "admin":
        return RedirectResponse("/home", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuario")
    usuarios = cursor.fetchall()
    db.close()
    return templates.TemplateResponse("usuarios.html", {"request": request, "usuarios": usuarios, "usuario": usuario})

@app.post("/usuarios_create")
def usuarios_create(request: Request, nombre: str = Form(...), correo: str = Form(...), password: str = Form(...), rol: str = Form(...)):
    usuario_session = request.session.get("usuario")
    if not usuario_session or usuario_session["rol"] != "admin":
        return RedirectResponse("/usuarios_web", status_code=303)
    
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
            "usuario": usuario_session,
            "error": "El correo ya está registrado en el sistema"
        })
    
    try:
        cursor.execute("INSERT INTO usuario (nombre, correo, password, rol) VALUES (%s,%s,%s,%s)",
                       (nombre, correo, password, rol))
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
            "usuario": usuario_session,
            "error": f"Error al crear usuario: {str(e)}"
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
@app.get("/reportes_web")
def reportes_web(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("reportes.html", {"request": request, "usuario": usuario})

@app.get("/descargar_vehiculos_csv")
def descargar_vehiculos_csv(request: Request):
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
def descargar_viajes_csv(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM viaje")
    viajes = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id_viaje', 'origen', 'destino', 'fecha_salida', 'estado'])
    writer.writeheader()
    writer.writerows(viajes)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=viajes.csv"}
    )

@app.get("/descargar_consumo_csv")
def descargar_consumo_csv(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM consumo")
    consumo = cursor.fetchall()
    db.close()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id_consumo', 'id_vehiculo', 'litros', 'fecha'])
    writer.writeheader()
    writer.writerows(consumo)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=consumo.csv"}
    )

# ==================== BUSQUEDA Y FILTROS ====================

@app.get("/vehiculos_web")
def vehiculos_web(request: Request, buscar: str = "", filtro_estado: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM vehiculo WHERE 1=1"
    params = []
    
    # Búsqueda por matrícula o modelo
    if buscar:
        query += " AND (matricula LIKE %s OR modelo LIKE %s OR marca LIKE %s)"
        params.extend([f"%{buscar}%", f"%{buscar}%", f"%{buscar}%"])
    
    # Filtro por estado
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

@app.get("/conductores_web")
def conductores_web(request: Request, buscar: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM conductor WHERE 1=1"
    params = []
    
    # Búsqueda por nombre o apellido
    if buscar:
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

@app.get("/viajes_web")
def viajes_web(request: Request, buscar: str = "", filtro_estado: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM viaje WHERE 1=1"
    params = []
    
    # Búsqueda por origen o destino
    if buscar:
        query += " AND (origen LIKE %s OR destino LIKE %s)"
        params.extend([f"%{buscar}%", f"%{buscar}%"])
    
    # Filtro por estado
    if filtro_estado:
        query += " AND estado = %s"
        params.append(filtro_estado)
    
    cursor.execute(query, params)
    viajes = cursor.fetchall()
    db.close()
    
    return templates.TemplateResponse("viajes.html", {
        "request": request, 
        "viajes": viajes, 
        "usuario": usuario,
        "buscar": buscar,
        "filtro_estado": filtro_estado
    })

@app.get("/mantenimiento_web")
def mantenimiento_web(request: Request, buscar: str = "", filtro_vehiculo: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM mantenimiento WHERE 1=1"
    params = []
    
    # Búsqueda por descripción
    if buscar:
        query += " AND descripcion LIKE %s"
        params.append(f"%{buscar}%")
    
    # Filtro por vehículo
    if filtro_vehiculo:
        query += " AND id_vehiculo = %s"
        params.append(int(filtro_vehiculo))
    
    cursor.execute(query, params)
    mant = cursor.fetchall()
    
    # Obtener lista de vehículos para el filtro
    cursor.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
    vehiculos_list = cursor.fetchall()
    db.close()
    
    return templates.TemplateResponse("mantenimiento.html", {
        "request": request, 
        "mantenimiento": mant, 
        "usuario": usuario,
        "buscar": buscar,
        "filtro_vehiculo": filtro_vehiculo,
        "vehiculos_list": vehiculos_list
    })

@app.get("/consumo_web")
def consumo_web(request: Request, buscar: str = "", filtro_vehiculo: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM consumo WHERE 1=1"
    params = []
    
    # Filtro por vehículo
    if filtro_vehiculo:
        query += " AND id_vehiculo = %s"
        params.append(int(filtro_vehiculo))
    
    cursor.execute(query, params)
    cons = cursor.fetchall()
    
    # Obtener lista de vehículos para el filtro
    cursor.execute("SELECT id_vehiculo, matricula FROM vehiculo ORDER BY matricula")
    vehiculos_list = cursor.fetchall()
    db.close()
    
    return templates.TemplateResponse("consumo.html", {
        "request": request, 
        "consumo": cons, 
        "usuario": usuario,
        "filtro_vehiculo": filtro_vehiculo,
        "vehiculos_list": vehiculos_list
    })

@app.get("/incidentes_web")
def incidentes_web(request: Request, buscar: str = "", filtro_tipo: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM incidente WHERE 1=1"
    params = []
    
    # Búsqueda por descripción
    if buscar:
        query += " AND descripcion LIKE %s"
        params.append(f"%{buscar}%")
    
    # Filtro por tipo
    if filtro_tipo:
        query += " AND tipo = %s"
        params.append(filtro_tipo)
    
    cursor.execute(query, params)
    inc = cursor.fetchall()
    db.close()
    
    return templates.TemplateResponse("incidentes.html", {
        "request": request, 
        "incidentes": inc, 
        "usuario": usuario,
        "buscar": buscar,
        "filtro_tipo": filtro_tipo
    })

@app.get("/ordenes_web")
def ordenes_web(request: Request, buscar: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM orden_servicio WHERE 1=1"
    params = []
    
    # Búsqueda por descripción
    if buscar:
        query += " AND descripcion LIKE %s"
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

@app.get("/flota_web")
def flota_web(request: Request, buscar: str = ""):
    usuario = request.session.get("usuario")
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM flota WHERE 1=1"
    params = []
    
    # Búsqueda por nombre
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
