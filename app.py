from flask import Flask, request, render_template_string, redirect, url_for, session
from dotenv import load_dotenv
import os
import base64
from functools import wraps
from supabase import create_client, Client

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "clave_secreta_para_sesiones_tienda_123")

# Credenciales del Administrador
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

# Conexión con Supabase (Lee dinámicamente las Variables de Entorno)
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bkxniuudzmxcpouzgqxm.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    supabase = None

# Decorador para proteger rutas exclusivas de administración
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Función auxiliar para procesar fotos subidas desde dispositivos
def procesar_foto(file_obj):
    if not file_obj or file_obj.filename == '':
        return None
    try:
        file_bytes = file_obj.read()
        filename = f"foto_{file_obj.filename}"
        supabase.storage.from_("productos").upload(filename, file_bytes, {"content-type": file_obj.content_type})
        return supabase.storage.from_("productos").get_public_url(filename)
    except Exception as e:
        try:
            file_obj.seek(0)
            encoded = base64.b64encode(file_obj.read()).decode('utf-8')
            return f"data:{file_obj.content_type};base64,{encoded}"
        except:
            return None

# =========================================================
# PLANTILLA BASE DEL PANEL ADMIN
# =========================================================
ADMIN_BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel de Control - Catálogo Digital</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --sidebar-bg: #0F172A;
            --sidebar-hover: #1E293B;
            --primary: #4F46E5;
            --primary-hover: #4338CA;
            --bg: #F8FAFC;
            --surface: #FFFFFF;
            --text-main: #1E293B;
            --text-muted: #64748B;
            --border: #E2E8F0;
            --danger: #EF4444;
            --radius: 12px;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        body { display: flex; min-height: 100vh; background-color: var(--bg); color: var(--text-main); }

        .sidebar {
            width: 260px;
            background-color: var(--sidebar-bg);
            padding: 24px 16px;
            color: #F8FAFC;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 0 12px 20px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 12px;
        }
        .brand i { font-size: 1.5rem; color: #818CF8; }
        .brand h2 { font-size: 1.1rem; font-weight: 700; }
        .brand p { font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; }

        .nav-btn {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border-radius: 8px;
            color: #94A3B8;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.2s;
        }
        .nav-btn:hover, .nav-btn.active { background-color: var(--sidebar-hover); color: #FFFFFF; }
        .nav-btn i { font-size: 1.1rem; width: 20px; text-align: center; }

        .nav-btn.logout-link {
            margin-top: auto;
            background: rgba(239, 68, 68, 0.15);
            color: #FCA5A5;
            border: 1px solid rgba(239, 68, 68, 0.2);
        }
        .nav-btn.logout-link:hover { background: var(--danger); color: white; }

        .main-content { flex: 1; padding: 32px; overflow-y: auto; }
        .header-title { margin-bottom: 24px; }
        .header-title h1 { font-size: 1.75rem; font-weight: 800; color: #0F172A; }
        .header-title p { color: var(--text-muted); font-size: 0.95rem; }

        .table-box, .form-box {
            background: var(--surface);
            padding: 24px;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        table { width: 100%; border-collapse: collapse; text-align: left; }
        th { padding: 12px 16px; background: #F8FAFC; color: var(--text-muted); font-size: 0.8rem; font-weight: 700; text-transform: uppercase; border-bottom: 1px solid var(--border); }
        td { padding: 16px; border-bottom: 1px solid var(--border); font-size: 0.9rem; vertical-align: middle; }
        
        input[type="text"], input[type="number"], input[type="password"], select, textarea {
            width: 100%; padding: 12px 16px; margin: 8px 0 20px; border: 1px solid var(--border);
            border-radius: 8px; font-size: 0.95rem; outline: none; transition: border-color 0.2s;
        }
        input:focus, textarea:focus { border-color: var(--primary); }
        
        .file-upload-wrapper {
            border: 2px dashed #CBD5E1;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            background: #F8FAFC;
            margin: 8px 0 20px;
            cursor: pointer;
        }
        .file-upload-wrapper:hover { border-color: var(--primary); background: #EEF2FF; }
        .file-upload-wrapper input[type="file"] { display: none; }

        .action-btn {
            padding: 12px 24px; background-color: var(--primary); color: white; border: none;
            border-radius: 8px; cursor: pointer; font-weight: 600; text-decoration: none; display: inline-block; font-size: 0.95rem;
        }
        .action-btn:hover { background-color: var(--primary-hover); }

        .img-preview-thumb { width: 50px; height: 50px; object-fit: cover; border-radius: 8px; border: 1px solid var(--border); }
        .alert-error { background-color: #FEF2F2; border: 1px solid #FCA5A5; color: #991B1B; padding: 14px; border-radius: 8px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="brand">
            <i class="fa-solid fa-store"></i>
            <div>
                <h2>Tienda de Ropa</h2>
                <p>Catálogo Admin</p>
            </div>
        </div>
        
        <a href="/admin" class="nav-btn"><i class="fa-solid fa-chart-pie"></i> Inicio</a>
        <a href="/pedidos" class="nav-btn"><i class="fa-solid fa-receipt"></i> Encargos / Pedidos</a>
        <a href="/productos" class="nav-btn"><i class="fa-solid fa-box-open"></i> Productos</a>
        <a href="/agregar" class="nav-btn"><i class="fa-solid fa-plus-circle"></i> Agregar producto</a>
        <a href="/buscar" class="nav-btn"><i class="fa-solid fa-magnifying-glass"></i> Buscar producto</a>
        <a href="/categorias" class="nav-btn"><i class="fa-solid fa-layer-group"></i> Categorías</a>
        <a href="/seguridad" class="nav-btn"><i class="fa-solid fa-users"></i> Clientes</a>

        <a href="/" class="nav-btn" target="_blank"><i class="fa-solid fa-globe"></i> Ver Catálogo Público</a>
        <a href="/logout" class="nav-btn logout-link"><i class="fa-solid fa-right-from-bracket"></i> Cerrar Sesión</a>
    </div>

    <div class="main-content">
        {% if error %}
            <div class="alert-error">
                <i class="fa-solid fa-triangle-exclamation"></i> <strong>Aviso:</strong> {{ error }}
            </div>
        {% endif %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

# =========================================================
# LOGIN Y LOGOUT
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user = request.form.get("username")
        password = request.form.get("password")
        if user == ADMIN_USER and password == ADMIN_PASS:
            session["logged_in"] = True
            return redirect(url_for("admin_index"))
        else:
            error = "Usuario o contraseña incorrectos."

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Iniciar Sesión - Administración</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
            body { background: #F8FAFC; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
            .login-card { background: white; padding
