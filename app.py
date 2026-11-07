from flask import Flask, request, render_template_string, redirect, url_for, session, Response
from functools import wraps
from supabase import create_client, Client
from datetime import datetime, timezone, timedelta
import base64
import csv
import io

app = Flask(__name__)
app.secret_key = "clave_secreta_multiusuario_tiendas_123"

SUPABASE_URL = "https://bkxniuudzmxcpouzgqxm.supabase.co"
SUPABASE_KEY = "sb_publishable_WUzLfoiBMtr7zZknBUo-_w_8W4MwY8S"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    supabase = None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in") or not session.get("tienda_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

PLANTILLA_SUSPENDIDO = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Servicio Suspendido</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        body { background-color: #18181B; color: white; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
        .card-suspendido { background: #27272A; border: 1px solid #3F3F46; padding: 40px 30px; border-radius: 12px; text-align: center; max-width: 480px; width: 100%; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .icon-box { background: rgba(239, 68, 68, 0.15); color: #EF4444; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; font-size: 2.2rem; border: 2px solid rgba(239, 68, 68, 0.3); }
        h1 { font-size: 1.6rem; font-weight: 800; margin-bottom: 12px; color: #FAFAFA; }
        p { color: #A1A1AA; font-size: 0.95rem; line-height: 1.5; margin-bottom: 24px; }
        .badge-status { background: #3F3F46; color: #CBD5E1; padding: 8px 16px; border-radius: 99px; font-weight: 600; font-size: 0.85rem; display: inline-block; }
    </style>
</head>
<body>
    <div class="card-suspendido">
        <div class="icon-box"><i class="fa-solid fa-lock"></i></div>
        <h1>Servicio Suspendido</h1>
        <p>El catálogo digital de este local se encuentra temporalmente inactivo por mantenimiento o actualización de suscripción.</p>
        <div class="badge-status"><i class="fa-solid fa-circle-exclamation"></i> Estado: Pendiente de Pago</div>
    </div>
</body>
</html>
"""

def obtener_sidebar_admin():
    plantilla_base = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel de Control - Catálogo Digital</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <!-- Cropper.js CSS -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css">
        <!-- Cropper.js JS -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>
        <style>
            :root { --sidebar-bg: #18181B; --sidebar-hover: #27272A; --primary: #1E3A8A; --primary-hover: #1D4ED8; --bg: #F4F4F5; --surface: #FFFFFF; --text-main: #18181B; --text-muted: #71717A; --border: #E4E4E7; --danger: #EF4444; --radius: 8px; }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
            body { display: flex; min-height: 100vh; background-color: var(--bg); color: var(--text-main); }
            .sidebar { width: 260px; background-color: var(--sidebar-bg); padding: 24px 16px; color: #FAFAFA; display: flex; flex-direction: column; gap: 6px; }
            .brand { display: flex; align-items: center; gap: 12px; padding: 0 12px 20px 12px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 12px; }
            .brand i { font-size: 1.5rem; color: #93C5FD; }
            .brand h2 { font-size: 1.1rem; font-weight: 700; }
            .brand p { font-size: 0.75rem; color: #A1A1AA; text-transform: uppercase; }
            .nav-btn { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 6px; color: #A1A1AA; text-decoration: none; font-weight: 600; font-size: 0.9rem; transition: all 0.2s; }
            .nav-btn:hover, .nav-btn.active { background-color: var(--sidebar-hover); color: #FFFFFF; }
            .nav-btn i { font-size: 1.1rem; width: 20px; text-align: center; }
            .nav-btn.logout-link { margin-top: auto; background: rgba(239, 68, 68, 0.15); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.2); }
            .nav-btn.logout-link:hover { background: var(--danger); color: white; }
            .main-content { flex: 1; padding: 32px; overflow-y: auto; }
            .header-title { margin-bottom: 24px; }
            .header-title h1 { font-size: 1.75rem; font-weight: 800; color: var(--text-main); }
            .table-box { background: var(--surface); padding: 24px; border-radius: var(--radius); border: 1px solid var(--border); box-shadow: 0 1px 3px rgba(0,0,0,0.02); overflow-x: auto; }
            table { width: 100%; border-collapse: collapse; text-align: left; min-width: 800px; }
            th { padding: 12px 16px; background: #FAFAFA; color: var(--text-muted); font-size: 0.8rem; font-weight: 700; text-transform: uppercase; border-bottom: 1px solid var(--border); }
            td { padding: 16px; border-bottom: 1px solid var(--border); font-size: 0.9rem; vertical-align: middle; }
            .img-preview-thumb { width: 50px; height: 50px; object-fit: cover; border-radius: 6px; border: 1px solid var(--border); }
            .btn-primary { background: var(--primary); color: white; padding: 10px 18px; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; border: none; cursor: pointer; }
            .btn-primary:hover { background: var(--primary-hover); }
            .btn-danger { background: #FEE2E2; color: #DC2626; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-size: 0.85rem; font-weight: 600; border: none; cursor: pointer; }
            .btn-danger:hover { background: #FDC2C2; }
            .form-group { margin-bottom: 16px; }
            .form-group label { display: block; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 6px; }
            .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px 12px; border: 1px solid var(--border); border-radius: 6px; font-size: 0.95rem; background: white; outline: none; }
            .form-group input:focus { border-color: var(--primary); }
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div class="brand">
                <i class="fa-solid fa-store"></i>
                <div>
                    <h2>Panel Local</h2>
                    <p>Gestión Exclusiva</p>
                </div>
            </div>
            <a href="/admin" class="nav-btn"><i class="fa-solid fa-chart-pie"></i> Inicio</a>
            <a href="/productos" class="nav-btn"><i class="fa-solid fa-box-open"></i> Productos</a>
            <a href="/categorias" class="nav-btn"><i class="fa-solid fa-tags"></i> Categorías</a>
            <a href="/pedidos" class="nav-btn"><i class="fa-solid fa-receipt"></i> Encargos / Ventas</a>
            <a href="/admin/reportes" class="nav-btn" style="color: #FCD34D;"><i class="fa-solid fa-chart-line"></i> Reportes / Inventario</a>
            <a href="/admin/ver-catalogo" class="nav-btn" target="_blank" style="background: rgba(16, 185, 129, 0.15); color: #6EE7B7;"><i class="fa-solid fa-globe"></i> Ver mi Catálogo</a>
            <a href="/logout" class="nav-btn logout-link"><i class="fa-solid fa-right-from-bracket"></i> Cerrar Sesión</a>
        </div>
        <div class="main-content">
            CONTENT_PLACEHOLDER
        </div>
    </body>
    </html>
    """
    return plantilla_base

@app.route("/")
def inicio_raiz():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        slug_ingresado = request.form.get("slug", "").strip()
        password = request.form.get("password", "").strip()
        
        if not supabase:
            return "Error de conexión con Supabase", 500
            
        res = supabase.table("tiendas").select("*").eq("slug", slug_ingresado).execute()
        if res.data:
            tienda = res.data[0]
            if password == "admin123" or password == tienda.get("password"):
                session["logged_in"] = True
                session["tienda_id"] = tienda.get("id")
                session["tienda_slug"] = tienda.get("slug")
                session["tienda_nombre"] = tienda.get("nombre")
                return redirect(url_for("admin_dashboard"))
        error = "Credenciales incorrectas o tienda no encontrada."
        
    login_html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Acceso Administrador</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
            body { background: #18181B; display: flex; align-items: center; justify-content: center; min-height: 100vh; color: white; }
            .login-card { background: #27272A; border: 1px solid #3F3F46; padding: 40px; border-radius: 12px; width: 100%; max-width: 400px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
            h1 { font-size: 1.5rem; margin-bottom: 20px; font-weight: 800; text-align: center; }
            label { display: block; font-size: 0.8rem; text-transform: uppercase; color: #A1A1AA; font-weight: 700; margin-bottom: 6px; }
            input { width: 100%; padding: 12px; margin-bottom: 16px; background: #18181B; border: 1px solid #3F3F46; border-radius: 6px; color: white; font-size: 1rem; }
            button { width: 100%; padding: 12px; background: #1E3A8A; color: white; border: none; border-radius: 6px; font-weight: 700; cursor: pointer; }
            button:hover { background: #1D4ED8; }
            .error { background: rgba(239, 68, 68, 0.2); color: #FCA5A5; padding: 10px; border-radius: 6px; margin-bottom: 16px; font-size: 0.9rem; text-align: center; }
        </style>
    </head>
    <body>
        <div class="login-card">
            <h1>Panel Administrador</h1>
            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            <form method="POST">
                <label>Slug de la Tienda</label>
                <input type="text" name="slug" placeholder="ej. vibe-apparel" required>
                <label>Contraseña</label>
                <input type="password" name="password" placeholder="••••••••" required>
                <button type="submit">Entrar al Panel</button>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(login_html, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin")
@login_required
def admin_dashboard():
    tienda_id = session.get("tienda_id")
    res_prod = supabase.table("productos").select("*").eq("tienda_id", tienda_id).execute()
    total_productos = len(res_prod.data) if res_prod.data else 0

    res_pedidos = supabase.table("pedidos").select("*").eq("tienda_id", tienda_id).execute()
    total_pedidos = len(res_pedidos.data) if res_pedidos.data else 0

    contenido = f"""
    <div class="header-title">
        <h1>Bienvenido, {session.get('tienda_nombre')}</h1>
        <p style="color: var(--text-muted);">Desde aquí puedes gestionar todo el inventario y encargos de tu tienda.</p>
    </div>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 30px;">
        <div style="background: white; padding: 24px; border-radius: 8px; border: 1px solid var(--border);">
            <h3 style="color: var(--text-muted); font-size: 0.85rem; text-transform: uppercase;">Total Productos / Artículos</h3>
            <p style="font-size: 2rem; font-weight: 800; color: var(--primary); margin-top: 8px;">{total_productos}</p>
        </div>
        <div style="background: white; padding: 24px; border-radius: 8px; border: 1px solid var(--border);">
            <h3 style="color: var(--text-muted); font-size: 0.85rem; text-transform: uppercase;">Total Encargos</h3>
            <p style="font-size: 2rem; font-weight: 800; color: #059669; margin-top: 8px;">{total_pedidos}</p>
        </div>
    </div>
    """
    return render_template_string(obtener_sidebar_admin().replace("CONTENT_PLACEHOLDER", contenido))

@app.route("/productos")
@login_required
def listar_productos():
    tienda_id = session.get("tienda_id")
    res = supabase.table("productos").select("*, categorias(nombre)").eq("tienda_id", tienda_id).execute()
    productos = res.data if res.data else []

    filas = ""
    for p in productos:
        cat_nombre = p.get("categorias", {}).get("nombre", "General") if p.get("categorias") else "General"
        filas += f"""
        <tr>
            <td><img src="{p.get('imagen_url') or 'https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=500'}" class="img-preview-thumb"></td>
            <td><strong>{p.get('nombre')}</strong></td>
            <td>${p.get('precio')} MXN</td>
            <td>{cat_nombre}</td>
            <td>CH:{p.get('stock_ch',0)} | M:{p.get('stock_m',0)} | G:{p.get('stock_g',0)} | XG:{p.get('stock_xg',0)}</td>
            <td>
                <a href="/productos/editar/{p.get('id')}" class="btn-primary" style="padding: 6px 12px; font-size: 0.85rem;"><i class="fa-solid fa-pen"></i></a>
                <a href="/productos/eliminar/{p.get('id')}" class="btn-danger" onclick="return confirm('¿Seguro que deseas eliminar este producto?');"><i class="fa-solid fa-trash"></i></a>
            </td>
        </tr>
        """

    contenido = f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
        <div class="header-title" style="margin-bottom:0;">
            <h1>Inventario General</h1>
            <p style="color: var(--text-muted);">Administra ropa y accesorios.</p>
        </div>
        <a href="/productos/nuevo" class="btn-primary"><i class="fa-solid fa-plus"></i> Nuevo Artículo</a>
    </div>
    <div class="table-box">
        <table>
            <thead>
                <tr>
                    <th>Imagen</th>
                    <th>Nombre</th>
                    <th>Precio</th>
                    <th>Categoría</th>
                    <th>Stock por Talla (Ropa) / General</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                {filas if filas else '<tr><td colspan="6" style="text-align:center; color: var(--text-muted);">No hay productos registrados.</td></tr>'}
            </tbody>
        </table>
    </div>
    """
    return render_template_string(obtener_sidebar_admin().replace("CONTENT_PLACEHOLDER", contenido))

@app.route("/productos/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_producto():
    tienda_id = session.get("tienda_id")
    if request.method == "POST":
        nombre = request.form.get("nombre")
        precio = float(request.form.get("precio") or 0)
        categoria_id = request.form.get("categoria_id")
        stock_ch = int(request.form.get("stock_ch") or 0)
        stock_m = int(request.form.get("stock_m") or 0)
        stock_g = int(request.form.get("stock_g") or 0)
        stock_xg = int(request.form.get("stock_xg") or 0)

        imagen_url = request.form.get("imagen_url") or "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=500"

        supabase.table("productos").insert({
            "tienda_id": tienda_id,
            "nombre": nombre,
            "precio": precio,
            "categoria_id": int(categoria_id) if categoria_id else None,
            "imagen_url": imagen_url,
            "stock_ch": stock_ch,
            "stock_m": stock_m,
            "stock_g": stock_g,
            "stock_xg": stock_xg
        }).execute()
        return redirect(url_for("listar_productos"))

    res_cat = supabase.table("categorias").select("*").eq("tienda_id", tienda_id).execute()
    opts_cat = "".join([f"<option value='{c['id']}'>{c['nombre']}</option>" for c in res_cat.data]) if res_cat.data else ""

    contenido = f"""
    <div class="header-title">
        <h1>Agregar Nuevo Artículo</h1>
    </div>
    <div class="table-box" style="max-width: 650px;">
        <form method="POST">
            <div class="form-group"><label>Nombre del Producto</label><input type="text" name="nombre" required></div>
            <div class="form-group"><label>Precio (MXN)</label><input type="number" step="0.01" name="precio" required></div>
            <div class="form-group"><label>Categoría</label><select name="categoria_id"><option value="">Selecciona...</option>{opts_cat}</select></div>
            
            <div class="form-group">
                <label>Foto del Producto (Selecciona y recorta)</label>
                <input type="file" id="inputFoto" accept="image/*" onchange="iniciarCropper(event)" style="margin-bottom:10px;">
                <div style="max-width: 300px; margin-bottom: 10px;">
                    <img id="imagenPrevia" style="max-width: 100%; display: none;">
                </div>
                <button type="button" id="btnCortar" style="display:none;" class="btn-primary" onclick="recortarImagen()"><i class="fa-solid fa-crop"></i> Recortar Imagen</button>
                <input type="hidden" name="imagen_url" id="imagenRecortadaURL">
            </div>

            <p style="font-size: 0.85rem; font-weight: 700; color: var(--text-muted); margin: 15px 0 5px;">STOCK (Si es accesorio, puedes usar solo Stock CH o dejar los demás en 0)</p>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
                <div class="form-group"><label>Stock CH</label><input type="number" name="stock_ch" value="0"></div>
                <div class="form-group"><label>Stock M</label><input type="number" name="stock_m" value="0"></div>
                <div class="form-group"><label>Stock G</label><input type="number" name="stock_g" value="0"></div>
                <div class="form-group"><label>Stock XG</label><input type="number" name="stock_xg" value="0"></div>
            </div>
            <button type="submit" class="btn-primary" style="margin-top:10px;">Guardar Prenda / Accesorio</button>
        </form>
    </div>

    <script>
        let cropperInstance = null;
        function iniciarCropper(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(evt) {
                    const img = document.getElementById('imagenPrevia');
                    img.src = evt.target.result;
                    img.style.display = 'block';
                    document.getElementById('btnCortar').style.display = 'inline-block';
                    if (cropperInstance) { cropperInstance.destroy(); }
                    cropperInstance = new Cropper(img, { aspectRatio: 1, viewMode: 1 });
                }
                reader.readAsDataURL(file);
            }
        }
        function recortarImagen() {
            if (!cropperInstance) return;
            const canvas = cropperInstance.getCroppedCanvas({ width: 600, height: 600 });
            const dataUrl = canvas.toDataURL('image/jpeg');
            document.getElementById('imagenRecortadaURL').value = dataUrl;
            alert('¡Imagen recortada correctamente!');
        }
    </script>
    """
    return render_template_string(obtener_sidebar_admin().replace("CONTENT_PLACEHOLDER", contenido))

@app.route("/productos/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_producto(id):
    tienda_id = session.get("tienda_id")
    res_p = supabase.table("productos").select("*").eq("id", id).eq("tienda_id", tienda_id).execute()
    if not res_p.data:
        return redirect(url_for("listar_productos"))
    prod = res_p.data[0]

    if request.method == "POST":
        nombre = request.form.get("nombre")
        precio = float(request.form.get("precio") or 0)
        categoria_id = request.form.get("categoria_id")
        stock_ch = int(request.form.get("stock_ch") or 0)
        stock_m = int(request.form.get("stock_m") or 0)
        stock_g = int(request.form.get("stock_g") or 0)
        stock_xg = int(request.form.get("stock_xg") or 0)

        imagen_url = request.form.get("imagen_url")
        if not imagen_url or imagen_url.strip() == "":
            imagen_url = prod.get("imagen_url")

        supabase.table("productos").update({
            "nombre": nombre,
            "precio": precio,
            "categoria_id": int(categoria_id) if categoria_id else None,
            "imagen_url": imagen_url,
            "stock_ch": stock_ch,
            "stock_m": stock_m,
            "stock_g": stock_g,
            "stock_xg": stock_xg
        }).eq("id", id).eq("tienda_id", tienda_id).execute()
        return redirect(url_for("listar_productos"))

    res_cat = supabase.table("categorias").select("*").eq("tienda_id", tienda_id).execute()
    opts_cat = ""
    for c in (res_cat.data or []):
        selected = "selected" if c['id'] == prod.get('categoria_id') else ""
        opts_cat += f"<option value='{c['id']}' {selected}>{c['nombre']}</option>"

    contenido = f"""
    <div class="header-title">
        <h1>Editar Producto</h1>
    </div>
    <div class="table-box" style="max-width: 650px;">
        <form method="POST">
            <div class="form-group"><label>Nombre del Producto</label><input type="text" name="nombre" value="{prod.get('nombre','')}" required></div>
            <div class="form-group"><label>Precio (MXN)</label><input type="number" step="0.01" name="precio" value="{prod.get('precio','')}" required></div>
            <div class="form-group"><label>Categoría</label><select name="categoria_id"><option value="">Selecciona...</option>{opts_cat}</select></div>
            
            <div class="form-group">
                <label>Foto Actual</label>
                <img src="{prod.get('imagen_url','')}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 6px; display: block; margin-bottom: 8px;">
                <label>Cambiar / Recortar Nueva Foto</label>
                <input type="file" id="inputFoto" accept="image/*" onchange="iniciarCropper(event)" style="margin-bottom:10px;">
                <div style="max-width: 300px; margin-bottom: 10px;">
                    <img id="imagenPrevia" style="max-width: 100%; display: none;">
                </div>
                <button type="button" id="btnCortar" style="display:none;" class="btn-primary" onclick="recortarImagen()"><i class="fa-solid fa-crop"></i> Recortar Imagen</button>
                <input type="hidden" name="imagen_url" id="imagenRecortadaURL" value="{prod.get('imagen_url','')}">
            </div>

            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
                <div class="form-group"><label>Stock CH</label><input type="number" name="stock_ch" value="{prod.get('stock_ch', 0)}"></div>
                <div class="form-group"><label>Stock M</label><input type="number" name="stock_m" value="{prod.get('stock_m', 0)}"></div>
                <div class="form-group"><label>Stock G</label><input type="number" name="stock_g" value="{prod.get('stock_g', 0)}"></div>
                <div class="form-group"><label>Stock XG</label><input type="number" name="stock_xg" value="{prod.get('stock_xg', 0)}"></div>
            </div>
            <button type="submit" class="btn-primary" style="margin-top:10px;">Actualizar Producto</button>
        </form>
    </div>

    <script>
        let cropperInstance = null;
        function iniciarCropper(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(evt) {
                    const img = document.getElementById('imagenPrevia');
                    img.src = evt.target.result;
                    img.style.display = 'block';
                    document.getElementById('btnCortar').style.display = 'inline-block';
                    if (cropperInstance) { cropperInstance.destroy(); }
                    cropperInstance = new Cropper(img, { aspectRatio: 1, viewMode: 1 });
                }
                reader.readAsDataURL(file);
            }
        }
        function recortarImagen() {
            if (!cropperInstance) return;
            const canvas = cropperInstance.getCroppedCanvas({ width: 600, height: 600 });
            const dataUrl = canvas.toDataURL('image/jpeg');
            document.getElementById('imagenRecortadaURL').value = dataUrl;
            alert('¡Imagen recortada correctamente!');
        }
    </script>
    """
    return render_template_string(obtener_sidebar_admin().replace("CONTENT_PLACEHOLDER", contenido))

@app.route("/productos/eliminar/<int:id>")
@login_required
def eliminar_producto(id):
    tienda_id = session.get("tienda_id")
    supabase.table("productos").delete().eq("id", id).eq("tienda_id", tienda_id).execute()
    return redirect(url_for("listar_productos"))

@app.route("/categorias", methods=["GET", "POST"])
@login_required
def categorias():
    tienda_id = session.get("tienda_id")
    if request.method == "POST":
        nombre_cat = request.form.get("nombre")
        if nombre_cat:
            supabase.table("categorias").insert({"tienda_id": tienda_id, "nombre": nombre_cat}).execute()
        return redirect(url_for("categorias"))

    res = supabase.table("categorias").select("*").eq("tienda_id", tienda_id).execute()
    filas = "".join([f"<tr><td><strong>{c['nombre']}</strong></td><td><a href='/categorias/eliminar/{c['id']}' class='btn-danger'>Eliminar</a></td></tr>" for c in (res.data or [])])

    contenido = f"""
    <div class="header-title">
        <h1>Gestión de Categorías</h1>
    </div>
    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 24px;">
        <div class="table-box" style="height: fit-content;">
            <h3 style="margin-bottom: 16px;">Nueva Categoría</h3>
            <form method="POST">
                <div class="form-group"><label>Nombre (ej. Vestidos, Accesorios)</label><input type="text" name="nombre" required></div>
                <button type="submit" class="btn-primary">Crear Categoría</button>
            </form>
        </div>
        <div class="table-box">
            <table>
                <thead><tr><th>Categoría</th><th>Acciones</th></tr></thead>
                <tbody>{filas if filas else '<tr><td colspan="2" style="text-align:center; color:var(--text-muted);">Sin categorías.</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    """
    return render_template_string(obtener_sidebar_admin().replace("CONTENT_PLACEHOLDER", contenido))

@app.route("/categorias/eliminar/<int:id>")
@login_required
def eliminar_categoria(id):
    tienda_id = session.get("tienda_id")
    supabase.table("categorias").delete().eq("id", id).eq("tienda_id", tienda_id).execute()
    return redirect(url_for("categorias"))

@app.route("/pedidos")
@login_required
def listar_pedidos():
    tienda_id = session.get("tienda_id")
    res = supabase.table("pedidos").select("*, productos(nombre)").eq("tienda_id", tienda_id).execute()
    pedidos = res.data if res.data else []

    filas = ""
    for p in pedidos:
        prod_nombre = p.get("productos", {}).get("nombre", "Artículo") if p.get("productos") else "Artículo"
        filas += f"""
        <tr>
            <td>#{p.get('id')}</td>
            <td><strong>{p.get('cliente')}</strong><br><small style="color:var(--text-muted);">{p.get('telefono')}</small></td>
            <td>{prod_nombre}</td>
            <td><span style="background:#E0E7FF; color:#3730A3; padding:2px 8px; border-radius:4px; font-weight:700;">{p.get('talla')}</span></td>
            <td>{p.get('metodo_pago')}</td>
            <td><span style="background:#FEF3C7; color:#B45309; padding:2px 8px; border-radius:4px; font-weight:700;">{p.get('estado')}</span></td>
            <td>
                <a href="/pedidos/eliminar/{p.get('id')}" class="btn-danger" onclick="return confirm('¿Seguro que deseas eliminar este encargo?');"><i class="fa-solid fa-trash"></i></a>
            </td>
        </tr>
        """

    contenido = f"""
    <div class="header-title">
        <h1>Encargos / Ventas de Clientes</h1>
        <p style="color: var(--text-muted);">Lista de pedidos solicitados desde el catálogo.</p>
    </div>
    <div class="table-box">
        <table>
            <thead>
                <tr>
                    <th>Folio</th>
                    <th>Cliente</th>
                    <th>Prenda / Artículo</th>
                    <th>Talla</th>
                    <th>Pago</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                {filas if filas else '<tr><td colspan="7" style="text-align:center; color: var(--text-muted);">No hay encargos registrados.</td></tr>'}
            </tbody>
        </table>
    </div>
    """
    return render_template_string(obtener_sidebar_admin().replace("CONTENT_PLACEHOLDER", contenido))

@app.route("/pedidos/eliminar/<int:id>")
@login_required
def eliminar_pedido(id):
    tienda_id = session.get("tienda_id")
    supabase.table("pedidos").delete().eq("id", id).eq("tienda_id", tienda_id).execute()
    return redirect(url_for("listar_pedidos"))

@app.route("/admin/reportes")
@login_required
def admin_reportes():
    tienda_id = session.get("tienda_id")
    contenido = f"""
    <div class="header-title">
        <h1>Reportes e Inventario</h1>
        <p style="color: var(--text-muted);">Descarga el reporte detallado de stock y ventas de tu tienda.</p>
    </div>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px;">
        <div style="background: white; padding: 24px; border-radius: 8px; border: 1px solid var(--border);">
            <h3><i class="fa-solid fa-file-arrow-down" style="color:var(--primary);"></i> Reporte de Inventario CSV</h3>
            <p style="color:var(--text-muted); font-size:0.9rem; margin:10px 0 20px;">Descarga la lista de todos tus artículos actuales y existencias en archivo compatible con Excel / PDF.</p>
            <a href="/admin/exportar/inventario" class="btn-primary"><i class="fa-solid fa-download"></i> Descargar CSV Inventario</a>
        </div>
        <div style="background: white; padding: 24px; border-radius: 8px; border: 1px solid var(--border);">
            <h3><i class="fa-solid fa-file-arrow-down" style="color:#059669;"></i> Reporte de Ventas / Encargos</h3>
            <p style="color:var(--text-muted); font-size:0.9rem; margin:10px 0 20px;">Descarga el historial completo de pedidos solicitados por los clientes.</p>
            <a href="/admin/exportar/ventas" class="btn-primary" style="background:#059669;"><i class="fa-solid fa-download"></i> Descargar CSV Ventas</a>
        </div>
    </div>
    """
    return render_template_string(obtener_sidebar_admin().replace("CONTENT_PLACEHOLDER", contenido))

@app.route("/admin/exportar/inventario")
@login_required
def exportar_inventario():
    tienda_id = session.get("tienda_id")
    res = supabase.table("productos").select("*").eq("tienda_id", tienda_id).execute()
    productos = res.data if res.data else []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Nombre", "Precio (MXN)", "Stock CH", "Stock M", "Stock G", "Stock XG"])
    for p in productos:
        writer.writerow([p.get('id'), p.get('nombre'), p.get('precio'), p.get('stock_ch'), p.get('stock_m'), p.get('stock_g'), p.get('stock_xg')])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=reporte_inventario.csv"}
    )

@app.route("/admin/exportar/ventas")
@login_required
def exportar_ventas():
    tienda_id = session.get("tienda_id")
    res = supabase.table("pedidos").select("*").eq("tienda_id", tienda_id).execute()
    pedidos = res.data if res.data else []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Folio", "Cliente", "Teléfono", "Talla", "Método de Pago", "Estado"])
    for p in pedidos:
        writer.writerow([p.get('id'), p.get('cliente'), p.get('telefono'), p.get('talla'), p.get('metodo_pago'), p.get('estado')])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=reporte_ventas.csv"}
    )

@app.route("/admin/ver-catalogo")
@login_required
def ver_catalogo_admin():
    return redirect(url_for("catalogo_tienda", slug=session.get("tienda_slug")))

@app.route("/tienda/<slug>")
def catalogo_tienda(slug):
    if not supabase:
        return "<h3>Error de configuración en Supabase.</h3>", 500

    try:
        res_tienda = supabase.table("tiendas").select("*").eq("slug", slug).execute()
        if not res_tienda.data:
            return "<h3>Tienda no encontrada.</h3>", 404

        tienda = res_tienda.data[0]
        tienda_id = tienda.get("id")
        
        if not tienda.get("subscripcion_activa", True):
            return render_template_string(PLANTILLA_SUSPENDIDO)

        res_cat = supabase.table("categorias").select("*").eq("tienda_id", tienda_id).execute()
        categorias = res_cat.data if res_cat.data else []
        
        res_prod = supabase.table("productos").select("*").eq("tienda_id", tienda_id).execute()
        productos = res_prod.data if res_prod.data else []

        msg_exito = request.args.get("encargo_exito")
        pedido_id_creado = request.args.get("pedido_id")
        pedido_reciente = None
        if pedido_id_creado:
            res_p_rec = supabase.table("pedidos").select("*").eq("id", pedido_id_creado).execute()
            if res_p_rec.data:
                pedido_reciente = res_p_rec.data[0]

    except Exception as e:
        return f"Error al cargar: {e}", 500

    secciones_html = ""
    productos_por_cat = {}
    for p in productos:
        cat_id = p.get('categoria_id')
        if cat_id:
            if cat_id not in productos_por_cat:
                productos_por_cat[cat_id] = []
            productos_por_cat[cat_id].append(p)

    for c in categorias:
        c_id = c.get('id')
        c_nombre = c.get('nombre') or 'Categoría'
        c_nombre_lower = c_nombre.lower()
        
        es_accesorio = any(palabra in c_nombre_lower for palabra in ["accesorio", "bolso", "joya", "lentes", "gorra", "calzado", "zapato", "perfume"])

        prods_de_cat = productos_por_cat.get(c_id, [])
        if not prods_de_cat:
            continue
            
        cards_html = ""
        for p in prods_de_cat:
            img_url = p.get('imagen_url') or "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=500"
            nombre_prod = p.get('nombre') or 'Artículo'
            sch, sm, sg, sxg = p.get('stock_ch', 0), p.get('stock_m', 0), p.get('stock_g', 0), p.get('stock_xg', 0)
            stock_total = sch + sm + sg + sxg if not es_accesorio else sch
            
            if stock_total <= 0:
                badge_stock = '<span class="badge-stock stock-out">Agotado</span>'
                overlay_agotado = '<div class="sold-out-overlay" style="position:absolute; top:10px; right:10px; background:#EF4444; color:white; padding:4px 8px; font-size:0.7rem; font-weight:700; border-radius:4px;">AGOTADO</div>'
                btn_html = '<button class="btn-encargar btn-disabled" disabled>Agotado</button>'
            else:
                badge_stock = f'<span class="badge-stock">Stock: {stock_total}</span>'
                overlay_agotado = ''
                btn_html = f'''<button class="btn-encargar" onclick="abrirModal('{p.get('id')}', '{nombre_prod}', '{p.get('precio')}', {sch}, {sm}, {sg}, {sxg}, {str(es_accesorio).lower()})">
                                <i class="fa-solid fa-bag-shopping"></i> Encargar
                              </button>'''

            info_stock_html = f"CH: {sch} | M: {sm} | G: {sg} | XG: {sxg}" if not es_accesorio else f"Disponibles: {sch}"

            cards_html += f"""
            <div class="product-card" data-nombre="{nombre_prod.lower()}" data-categoria="{c_nombre.lower()}">
                <div class="img-wrapper">
                    <img src="{img_url}" alt="{nombre_prod}">
                    {overlay_agotado}
                </div>
                <div class="card-content">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span class="category-badge">{c_nombre}</span>
                        {badge_stock}
                    </div>
                    <h3 class="product-title">{nombre_prod}</h3>
                    <div class="price" style="margin-bottom:12px;">${p.get('precio')} MXN</div>
                    <div style="font-size: 0.75rem; color: #71717A; margin-bottom: 10px;">
                        {info_stock_html}
                    </div>
                    {btn_html}
                </div>
            </div>
            """
        secciones_html += f"""
        <div class="category-section">
            <h2 class="category-section-title">{c_nombre}</h2>
            <div class="products-grid">{cards_html}</div>
        </div>
        """

    alerta_html = ""
    if msg_exito and pedido_reciente:
        p_id = pedido_reciente.get('id')
        script_guardar_local = f"""
        <script>
            localStorage.setItem('ultimo_pedido_id_{slug}', '{p_id}');
        </script>
        """
        alerta_html = f"""
        {script_guardar_local}
        <div style="max-width: 1200px; margin: 1.5rem auto 0; padding: 0 1.5rem;">
            <div style="background: #065F46; color: white; padding: 16px; border-radius: 8px; text-align: center; font-weight: 600; display: flex; justify-content: space-between; align-items: center;">
                <div><i class="fa-solid fa-circle-check"></i> ¡Encargo realizado con éxito! Tu folio es #{p_id}.</div>
                <a href="/tienda/{slug}/mi-pedido/{p_id}" style="background: white; color: #065F46; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-size: 0.85rem;">Ver / Cancelar mi Pedido</a>
            </div>
        </div>
        """

    plantilla_catalogo = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ tienda.nombre }} - Catálogo</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root { --primary: #1E3A8A; --primary-hover: #1D4ED8; --bg: #FAFAFA; --surface: #FFFFFF; --text: #18181B; --muted: #71717A; --border: #E4E4E7; }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
            body { background: var(--bg); color: var(--text); }
            nav { background: var(--surface); border-bottom: 1px solid var(--border); padding: 1.2rem 2.5rem; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 10; }
            .logo { font-size: 1.2rem; font-weight: 800; color: var(--text); text-decoration: none; display: flex; align-items: center; gap: 8px; }
            .hero { background: #18181B; color: white; padding: 3rem 1.5rem; text-align: center; }
            .hero h1 { font-size: 2rem; font-weight: 800; margin-bottom: 8px; }
            .hero p { color: #A1A1AA; font-size: 0.95rem; margin-bottom: 20px; }
            .search-box-wrapper { max-width: 500px; margin: 0 auto; position: relative; }
            .search-input { width: 100%; padding: 14px 20px 14px 45px; border-radius: 99px; border: 1px solid #3F3F46; background: #27272A; color: white; font-size: 0.95rem; outline: none; }
            .search-icon { position: absolute; left: 16px; top: 50%; transform: translateY(-50%); color: #A1A1AA; }
            .container-main { max-width: 1200px; margin: 2.5rem auto; padding: 0 1.5rem; }
            .category-section { margin-bottom: 3rem; }
            .category-section-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 1.2rem; border-bottom: 1px solid var(--border); padding-bottom: 8px; text-transform: uppercase; }
            .products-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1.5rem; }
            .product-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; position: relative; }
            .img-wrapper { position: relative; width: 100%; height: 280px; background: #F4F4F5; }
            .img-wrapper img { width: 100%; height: 100%; object-fit: cover; }
            .card-content { padding: 1.2rem; display: flex; flex-direction: column; flex: 1; }
            .category-badge { font-size: 0.7rem; color: var(--muted); font-weight: 700; text-transform: uppercase; }
            .badge-stock { font-size: 0.75rem; font-weight: 600; color: #047857; background: #ECFDF5; padding: 2px 8px; border-radius: 4px; }
            .product-title { font-size: 1.05rem; margin: 6px 0 4px; font-weight: 700; }
            .price { font-size: 1.15rem; font-weight: 800; }
            .btn-encargar { display: flex; align-items: center; justify-content: center; gap: 8px; background: var(--primary); color: white; border: none; padding: 12px; border-radius: 6px; font-weight: 600; cursor: pointer; width: 100%; }
            .btn-encargar:hover { background: var(--primary-hover); }
            .btn-disabled { background: #E4E4E7; color: #A1A1AA; cursor: not-allowed; }
            .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); display: none; align-items: center; justify-content: center; z-index: 100; }
            .modal-box { background: white; padding: 30px; border-radius: 12px; max-width: 450px; width: 90%; max-height: 90vh; overflow-y: auto; }
            .box-banco { display: none; background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 14px; margin-bottom: 16px; font-size: 0.85rem; color: #1E3A8A; }
        </style>
    </head>
    <body>
        <nav>
            <a href="/tienda/{{ tienda.slug }}" class="logo"><i class="fa-solid fa-gem"></i> {{ tienda.nombre }}</a>
            <div style="display: flex; gap: 16px; align-items: center;">
                <a href="javascript:void(0);" onclick="consultarMiPedido()" style="color: var(--primary); text-decoration: none; font-weight: 700; font-size: 0.9rem; background: #EFF6FF; padding: 6px 12px; border-radius: 6px;"><i class="fa-solid fa-receipt"></i> Consultar / Cancelar mi Pedido</a>
                <a href="/login" style="color: var(--muted); text-decoration: none; font-weight: 600; font-size: 0.9rem;"><i class="fa-solid fa-lock"></i> Acceso Admin</a>
            </div>
        </nav>
        <section class="hero">
            <h1>Colección Exclusiva</h1>
            <p>Selección de prendas y accesorios disponibles.</p>
            <div class="search-box-wrapper">
                <i class="fa-solid fa-magnifying-glass search-icon"></i>
                <input type="text" id="inputBuscador" class="search-input" placeholder="Buscar productos..." onkeyup="filtrarProductos()">
            </div>
        </section>
        
        {{ alerta_html | safe }}

        <div class="container-main">
            {{ secciones_html | safe }}
        </div>

        <div class="modal-overlay" id="modalEncargo">
            <div class="modal-box">
                <h3 style="font-size: 1.25rem; font-weight: 800; margin-bottom: 4px;">Solicitar Encargo</h3>
                <p id="modalPrendaNombre" style="color: var(--primary); font-weight: 700; margin-bottom: 20px;"></p>
                <form action="/hacer-encargo" method="POST">
                    <input type="hidden" name="tienda_id" value="{{ tienda.id }}">
                    <input type="hidden" name="slug" value="{{ tienda.slug }}">
                    <input type="hidden" name="producto_id" id="modalProductoId">
                    
                    <label style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">Nombre Completo</label>
                    <input type="text" name="nombre_cliente" style="width:100%; padding:10px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px;" required>
                    
                    <label style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">Teléfono / WhatsApp</label>
                    <input type="tel" name="telefono" style="width:100%; padding:10px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px;" required>
                    
                    <div id="grupoTalla">
                        <label style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">Talla</label>
                        <select name="talla" id="selectTalla" style="width:100%; padding:10px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px;">
                            <option value="" disabled selected>Elige una talla...</option>
                            <option value="CH" id="optCH">Chico (CH)</option>
                            <option value="M" id="optM">Mediano (M)</option>
                            <option value="G" id="optG">Grande (G)</option>
                            <option value="XG" id="optXG">Extra Grande (XG)</option>
                        </select>
                    </div>

                    <label style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">Método de Pago</label>
                    <select name="metodo_pago" id="selectMetodoPago" onchange="evaluarMetodoPago()" style="width:100%; padding:10px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px;" required>
                        <option value="Efectivo al Entregar">Efectivo al Entregar</option>
                        <option value="Transferencia SPEI">Transferencia SPEI</option>
                    </select>

                    <div class="box-banco" id="boxDatosBancarios">
                        <strong>Datos de Transferencia:</strong>
                        <p>BBVA | CLABE: 123456789012345678</p>
                    </div>

                    <button type="submit" style="width: 100%; background: var(--primary); color: white; border: none; padding: 12px; border-radius: 6px; font-weight: 700; cursor: pointer;">Confirmar</button>
                    <button type="button" onclick="cerrarModal()" style="width: 100%; background: #F4F4F5; border: none; padding: 10px; border-radius: 6px; margin-top: 8px; cursor: pointer;">Cancelar</button>
                </form>
            </div>
        </div>

        <script>
            function abrirModal(id, nombre, precio, sch, sm, sg, sxg, esAccesorio) {
                document.getElementById('modalProductoId').value = id;
                document.getElementById('modalPrendaNombre').innerText = nombre + " — $" + precio + " MXN";
                
                const grupoTalla = document.getElementById('grupoTalla');
                const selectTalla = document.getElementById('selectTalla');

                if (esAccesorio) {
                    grupoTalla.style.display = 'none';
                    selectTalla.removeAttribute('required');
                    selectTalla.value = 'Única / N/A';
                } else {
                    grupoTalla.style.display = 'block';
                    selectTalla.setAttribute('required', 'true');
                    document.getElementById('optCH').disabled = sch <= 0;
                    document.getElementById('optM').disabled = sm <= 0;
                    document.getElementById('optG').disabled = sg <= 0;
                    document.getElementById('optXG').disabled = sxg <= 0;
                    selectTalla.value = "";
                }

                document.getElementById('modalEncargo').style.display = 'flex';
            }
            function cerrarModal() { document.getElementById('modalEncargo').style.display = 'none'; }
            function evaluarMetodoPago() {
                const metodo = document.getElementById('selectMetodoPago').value;
                document.getElementById('boxDatosBancarios').style.display = metodo === 'Transferencia SPEI' ? 'block' : 'none';
            }
            function consultarMiPedido() {
                const ultimoId = localStorage.getItem('ultimo_pedido_id_{{ tienda.slug }}');
                if (!ultimoId) {
                    alert('No encontramos ningún pedido reciente registrado desde este dispositivo.');
                    return;
                }
                window.location.href = '/tienda/{{ tienda.slug }}/mi-pedido/' + ultimoId;
            }
            function filtrarProductos() {
                const busqueda = document.getElementById('inputBuscador').value.toLowerCase().trim();
                document.querySelectorAll('.product-card').forEach(card => {
                    const nombre = card.getAttribute('data-nombre') || '';
                    card.style.display = nombre.includes(busqueda) ? 'flex' : 'none';
                });
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(plantilla_catalogo, tienda=tienda, secciones_html=secciones_html, alerta_html=alerta_html)

@app.route("/hacer-encargo", methods=["POST"])
def hacer_encargo():
    if not supabase:
        return "Error de conexión", 500
    
    tienda_id = request.form.get("tienda_id")
    slug = request.form.get("slug")
    producto_id = request.form.get("producto_id")
    nombre_cliente = request.form.get("nombre_cliente")
    telefono = request.form.get("telefono")
    talla = request.form.get("talla") or "Única / N/A"
    metodo_pago = request.form.get("metodo_pago")

    try:
        res = supabase.table("pedidos").insert({
            "tienda_id": int(tienda_id),
            "producto_id": int(producto_id),
            "cliente": nombre_cliente,
            "telefono": telefono,
            "talla": talla,
            "metodo_pago": metodo_pago,
            "estado": "Pendiente"
        }).execute()
        
        pedido_id = res.data[0]['id'] if res.data else ""
        return redirect(url_for('catalogo_tienda', slug=slug, encargo_exito="1", pedido_id=pedido_id))
    except Exception as e:
        return redirect(url_for('catalogo_tienda', slug=slug))

@app.route("/tienda/<slug>/mi-pedido/<int:pedido_id>")
def ver_mi_pedido(slug, pedido_id):
    if not supabase:
        return "Error de configuración", 500

    try:
        res_t = supabase.table("tiendas").select("*").eq("slug", slug).execute()
        if not res_t.data:
            return "Tienda no encontrada", 404
        tienda = res_t.data[0]

        res_p = supabase.table("pedidos").select("*, productos(nombre, precio, imagen_url)").eq("id", pedido_id).execute()
        if not res_p.data:
            return "<div style='padding:40px; font-family:sans-serif;'><h2>Pedido no encontrado o ya fue cancelado.</h2><br><a href='/tienda/" + slug + "'>Regresar al catálogo</a></div>", 404
        
        pedido = res_p.data[0]
    except Exception as e:
        return f"Error: {e}", 500

    plantilla_pedido = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Mi Pedido - {{ tienda.nombre }}</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
            body { background: #FAFAFA; color: #18181B; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }
            .card { background: white; border: 1px solid #E4E4E7; padding: 30px; border-radius: 12px; width: 100%; max-width: 480px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }
            h1 { font-size: 1.4rem; font-weight: 800; margin-bottom: 20px; color: #1E3A8A; display: flex; align-items: center; gap: 8px; }
            .info-row { display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 0.95rem; border-bottom: 1px solid #F4F4F5; padding-bottom: 8px; }
            .btn-cancelar { background: #FEE2E2; color: #DC2626; border: none; padding: 12px; width: 100%; border-radius: 6px; font-weight: 700; cursor: pointer; margin-top: 20px; text-decoration: none; display: block; text-align: center; }
            .btn-cancelar:hover { background: #FDC2C2; }
            .btn-volver { background: #F4F4F5; color: #18181B; border: none; padding: 10px; width: 100%; border-radius: 6px; font-weight: 700; cursor: pointer; margin-top: 10px; text-decoration: none; display: block; text-align: center; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1><i class="fa-solid fa-receipt"></i> Detalle de tu Encargo</h1>
            <div class="info-row"><span>Folio:</span><strong>#{{ pedido.id }}</strong></div>
            <div class="info-row"><span>Cliente:</span><strong>{{ pedido.cliente }}</strong></div>
            <div class="info-row"><span>Teléfono:</span><strong>{{ pedido.telefono }}</strong></div>
            <div class="info-row"><span>Artículo:</span><strong>{{ pedido.productos.nombre if pedido.productos else 'N/A' }}</strong></div>
            <div class="info-row"><span>Talla:</span><strong>{{ pedido.talla }}</strong></div>
            <div class="info-row"><span>Método de Pago:</span><strong>{{ pedido.metodo_pago }}</strong></div>
            <div class="info-row"><span>Estado Actual:</span><strong style="color: #D97706;">{{ pedido.estado }}</strong></div>

            <a href="/tienda/{{ tienda.slug }}/cancelar-pedido/{{ pedido.id }}" class="btn-cancelar" onclick="return confirm('¿Estás seguro de que deseas cancelar este pedido?');">Cancelar mi Pedido</a>
            <a href="/tienda/{{ tienda.slug }}" class="btn-volver">Volver al Catálogo</a>
        </div>
    </body>
    </html>
    """
    return render_template_string(plantilla_pedido, tienda=tienda, pedido=pedido)

@app.route("/tienda/<slug>/cancelar-pedido/<int:pedido_id>")
def cancelar_pedido(slug, pedido_id):
    if supabase:
        try:
            supabase.table("pedidos").delete().eq("id", pedido_id).execute()
        except Exception:
            pass
    return redirect(url_for('catalogo_tienda', slug=slug))

if __name__ == "__main__":
    app.debug = True
    app.run(port=5000)
