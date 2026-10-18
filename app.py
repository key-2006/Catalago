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

# Conexión con Supabase desde Variables de Entorno
SUPABASE_URL = "https://bkxniuudzmxcpouzgqxm.supabase.co"
SUPABASE_KEY = "sb_publishable_WUzLfoiBMtr7zZknBUo-_w_8W4MwY8S"

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
                <h2>Vibe Apparel</h2>
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
            .login-card { background: white; padding: 32px; border-radius: 16px; border: 1px solid #E2E8F0; width: 100%; max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
            .login-card h2 { color: #0F172A; font-size: 1.5rem; font-weight: 700; margin-bottom: 8px; text-align: center; }
            .login-card p { color: #64748B; font-size: 0.9rem; margin-bottom: 24px; text-align: center; }
            input { width: 100%; padding: 12px; margin: 8px 0 16px; border: 1px solid #CBD5E1; border-radius: 8px; font-size: 0.95rem; outline: none; }
            button { width: 100%; padding: 12px; background: #4F46E5; color: white; border: none; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 0.95rem; }
            button:hover { background: #4338CA; }
            .error-box { background: #FEF2F2; color: #991B1B; padding: 10px; border-radius: 8px; font-size: 0.85rem; margin-bottom: 16px; text-align: center; }
        </style>
    </head>
    <body>
        <div class="login-card">
            <h2>Acceso Administrador</h2>
            <p>Ingresa tus datos para gestionar la tienda</p>
            {% if error %}<div class="error-box">{{ error }}</div>{% endif %}
            <form method="POST">
                <label style="font-size: 0.85rem; font-weight: 600;">Usuario:</label>
                <input type="text" name="username" required placeholder="Ej. admin">
                
                <label style="font-size: 0.85rem; font-weight: 600;">Contraseña:</label>
                <input type="password" name="password" required placeholder="••••••••">
                
                <button type="submit">Entrar al Panel</button>
            </form>
        </div>
    </body>
    </html>
    """, error=error)

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("catalogo_publico"))

# =========================================================
# VISTA PÚBLICA DE CLIENTES (CATÁLOGO DIGITAL)
# =========================================================
@app.route("/")
def catalogo_publico():
    productos = []
    categorias = []
    cat_id_sel = request.args.get("cat")
    msg_exito = request.args.get("encargo_exito")
    
    try:
        res_cat = supabase.table("categorias").select("*").execute()
        categorias = res_cat.data if res_cat.data else []
        
        res_prod = supabase.table("productos").select("*").execute()
        todos_productos = res_prod.data if res_prod.data else []

        if cat_id_sel:
            nombre_cat_buscada = ""
            for c in categorias:
                if str(c.get("id")) == str(cat_id_sel):
                    nombre_cat_buscada = c.get("nombre", "").lower()
                    break

            for p in todos_productos:
                p_cat_id = str(p.get("categoria_id") or p.get("id_categoria") or "")
                p_cat_nom = str(p.get("categoria") or p.get("nombre") or "").lower()
                if p_cat_id == str(cat_id_sel) or (nombre_cat_buscada and nombre_cat_buscada in p_cat_nom):
                    productos.append(p)
        else:
            productos = todos_productos

    except Exception as e:
        productos = []

    cards_html = ""
    for p in productos:
        img_url = p.get('imagen_url') or p.get('imagen') or "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=500"
        stock_cant = p.get('stock') if p.get('stock') is not None else 1
        
        if stock_cant <= 0:
            badge_stock = '<span class="badge-stock stock-out">Agotado</span>'
            overlay_agotado = '<div class="sold-out-overlay">AGOTADO</div>'
            btn_html = f'<button class="btn-encargar btn-disabled" disabled><i class="fa-solid fa-ban"></i> Prenda Agotada</button>'
            img_class = "img-grayscale"
        else:
            badge_stock = f'<span class="badge-stock stock-in">Quedan {stock_cant} pza{"s" if stock_cant > 1 else ""}</span>'
            overlay_agotado = ''
            btn_html = f'''<button class="btn-encargar" onclick="abrirModal('{p.get('id')}', '{p.get('nombre')}', '{p.get('precio')}')">
                            <i class="fa-solid fa-bag-shopping"></i> Encargar Prenda
                          </button>'''
            img_class = ""
        
        cards_html += f"""
        <div class="product-card">
            <div class="img-wrapper">
                <img src="{img_url}" alt="{p.get('nombre')}" class="{img_class}">
                {overlay_agotado}
            </div>
            <div class="card-content">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span class="category-badge">Disponible</span>
                    {badge_stock}
                </div>
                <h3 class="product-title">{p.get('nombre')}</h3>
                <div class="price-row">
                    <span class="price">${p.get('precio')} MXN</span>
                </div>
                {btn_html}
            </div>
        </div>
        """

    active_all = 'active-cat' if not cat_id_sel else ''
    cat_html = f'<li class="cat-item"><a href="/" class="{active_all}">Todas las prendas</a></li>'
    
    for c in categorias:
        cat_id = c.get('id')
        nombre_cat = c.get('nombre') or c.get('nombre_categoria') or 'Categoría'
        active_class = 'active-cat' if str(cat_id_sel) == str(cat_id) else ''
        cat_html += f'<li class="cat-item"><a href="/?cat={cat_id}" class="{active_class}">{nombre_cat}</a></li>'

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Vibe Apparel - Catálogo Digital</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root {{ --primary: #4F46E5; --bg: #F8FAFC; --surface: #FFFFFF; --text: #0F172A; --muted: #64748B; }}
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }}
            body {{ background: var(--bg); color: var(--text); }}
            
            nav {{ background: var(--surface); border-bottom: 1px solid #E2E8F0; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 10; }}
            .logo {{ font-size: 1.3rem; font-weight: 800; color: var(--primary); text-decoration: none; display: flex; align-items: center; gap: 8px; }}
            
            .hero {{ background: linear-gradient(135deg, #4F46E5, #7C3AED); color: white; padding: 2.5rem 1.5rem; text-align: center; margin: 1.5rem auto; max-width: 1200px; border-radius: 16px; }}
            .hero h1 {{ font-size: 2.2rem; font-weight: 800; margin-bottom: 8px; }}

            .payments-bar {{ background: #FFFFFF; border: 1px solid #E2E8F0; max-width: 1200px; margin: 0 auto 1.5rem; padding: 1rem; border-radius: 12px; display: flex; align-items: center; justify-content: space-around; flex-wrap: wrap; gap: 1rem; }}
            .payment-item {{ display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 0.85rem; color: #475569; }}
            .payment-item i {{ color: #4F46E5; font-size: 1.1rem; }}

            .layout {{ max-width: 1200px; margin: 0 auto 2rem; padding: 0 1.5rem; display: grid; grid-template-columns: 240px 1fr; gap: 2rem; }}
            .sidebar-cat {{ background: var(--surface); padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; height: fit-content; }}
            .cat-list {{ list-style: none; margin-top: 1rem; }}
            .cat-item a {{ display: block; padding: 8px 12px; color: var(--muted); text-decoration: none; border-radius: 6px; font-weight: 500; transition: all 0.2s; }}
            .cat-item a:hover, .cat-item a.active-cat {{ background: #EEF2FF; color: var(--primary); font-weight: 700; }}

            .products-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 1.5rem; }}
            .product-card {{ background: var(--surface); border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden; display: flex; flex-direction: column; position: relative; }}
            
            .img-wrapper {{ position: relative; width: 100%; height: 220px; background: #E2E8F0; overflow: hidden; }}
            .img-wrapper img {{ width: 100%; height: 100%; object-fit: cover; }}
            .img-grayscale {{ filter: grayscale(100%) opacity(0.6); }}

            .sold-out-overlay {{
                position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-12deg);
                background: #EF4444; color: white; font-weight: 900; font-size: 1.4rem; letter-spacing: 3px;
                padding: 8px 28px; border-radius: 6px; box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4); border: 2px solid white; pointer-events: none; z-index: 5;
            }}

            .card-content {{ padding: 1rem; display: flex; flex-direction: column; flex: 1; }}
            .category-badge {{ font-size: 0.75rem; color: var(--primary); font-weight: 700; text-transform: uppercase; }}
            .badge-stock {{ font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 99px; }}
            .stock-in {{ background: #DCFCE7; color: #15803D; }}
            .stock-out {{ background: #FEE2E2; color: #B91C1C; }}

            .product-title {{ font-size: 1rem; margin: 6px 0 12px; font-weight: 700; }}
            .price {{ font-size: 1.2rem; font-weight: 800; color: var(--text); }}
            .btn-encargar {{ display: flex; align-items: center; justify-content: center; gap: 8px; background: #4F46E5; color: white; border: none; padding: 11px; border-radius: 8px; font-weight: 600; margin-top: 12px; cursor: pointer; transition: background 0.2s; }}
            .btn-encargar:hover {{ background: #4338CA; }}
            .btn-disabled {{ background: #94A3B8 !important; cursor: not-allowed; }}

            .modal-overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: none; align-items: center; justify-content: center; z-index: 100; }}
            .modal-box {{ background: white; padding: 24px; border-radius: 16px; max-width: 450px; width: 90%; }}
            .modal-box h3 {{ margin-bottom: 8px; font-size: 1.2rem; }}
            .modal-box input, .modal-box textarea {{ width: 100%; padding: 10px; margin: 6px 0 14px; border: 1px solid #CBD5E1; border-radius: 8px; }}
            .alert-toast {{ background: #10B981; color: white; padding: 12px 20px; border-radius: 8px; max-width: 1200px; margin: 0 auto 1rem; font-weight: 600; text-align: center; }}
        </style>
    </head>
    <body>
        <nav>
            <a href="/" class="logo"><i class="fa-solid fa-shirt"></i> Vibe Apparel</a>
            <a href="/admin" style="color: var(--muted); text-decoration: none; font-weight: 600;"><i class="fa-solid fa-lock"></i> Panel Admin</a>
        </nav>

        <section class="hero">
            <h1>Catálogo de Prendas Disponibles</h1>
            <p>Explora nuestras prendas en existencia y haz tu encargo en línea fácil y rápido.</p>
        </section>

        {'<div class="alert-toast">¡Tu encargo ha sido enviado con éxito! Te contactaremos pronto.</div>' if msg_exito else ''}

        <div class="payments-bar">
            <div class="payment-item"><i class="fa-solid fa-money-bill-wave"></i> Efectivo al Entregar</div>
            <div class="payment-item"><i class="fa-solid fa-credit-card"></i> Tarjetas de Débito / Crédito</div>
            <div class="payment-item"><i class="fa-solid fa-mobile-screen"></i> Transferencia SPEI</div>
        </div>

        <div class="layout">
            <aside class="sidebar-cat">
                <h3>Categorías</h3>
                <ul class="cat-list">
                    {cat_html}
                </ul>
            </aside>

            <main class="products-grid">
                {cards_html if cards_html else '<p style="grid-column: 1/-1; text-align: center; color: #64748B; padding: 2rem;">No hay prendas registradas en esta categoría.</p>'}
            </main>
        </div>

        <div class="modal-overlay" id="modalEncargo">
            <div class="modal-box">
                <h3>Encargar Prenda</h3>
                <p id="modalPrendaNombre" style="color: #4F46E5; font-weight: 700; margin-bottom: 12px;"></p>
                <form action="/hacer-encargo" method="POST">
                    <input type="hidden" name="producto_id" id="modalProductoId">
                    <label style="font-size: 0.85rem; font-weight: 600;">Tu Nombre Completo:</label>
                    <input type="text" name="nombre_cliente" placeholder="Ej. María López" required>
                    <label style="font-size: 0.85rem; font-weight: 600;">Teléfono / WhatsApp de contacto:</label>
                    <input type="tel" name="telefono" placeholder="Ej. 9811234567" required>
                    <label style="font-size: 0.85rem; font-weight: 600;">Notas o Talla deseada:</label>
                    <textarea name="notas" rows="3" placeholder="Ej. Talla M, paso a recoger por la tarde"></textarea>
                    <div style="display: flex; gap: 10px; margin-top: 10px;">
                        <button type="submit" style="flex: 1; background: #4F46E5; color: white; border: none; padding: 10px; border-radius: 8px; font-weight: 600; cursor: pointer;">Confirmar Encargo</button>
                        <button type="button" onclick="cerrarModal()" style="background: #E2E8F0; color: #475569; border: none; padding: 10px 16px; border-radius: 8px; font-weight: 600; cursor: pointer;">Cancelar</button>
                    </div>
                </form>
            </div>
        </div>

        <script>
            function abrirModal(id, nombre, precio) {{
                document.getElementById('modalProductoId').value = id;
                document.getElementById('modalPrendaNombre').innerText = nombre + " - $" + precio + " MXN";
                document.getElementById('modalEncargo').style.display = 'flex';
            }}
            function cerrarModal() {{
                document.getElementById('modalEncargo').style.display = 'none';
            }}
        </script>
    </body>
    </html>
    """)

# =========================================================
# REGISTRAR ENCARGO Y DESCONTAR STOCK
# =========================================================
@app.route("/hacer-encargo", methods=["POST"])
def hacer_encargo():
    producto_id = request.form.get("producto_id")
    nombre_cliente = request.form.get("nombre_cliente")
    telefono = request.form.get("telefono")
    notas = request.form.get("notas")
    
    try:
        supabase.table("pedidos").insert({
            "cliente": nombre_cliente,
            "telefono": telefono,
            "notas": notas,
            "producto_id": producto_id,
            "estado": "Pendiente"
        }).execute()
        
        res_prod = supabase.table("productos").select("stock").eq("id", producto_id).execute()
        if res_prod.data:
            stock_actual = res_prod.data[0].get('stock') if res_prod.data[0].get('stock') is not None else 1
            nuevo_stock = max(0, stock_actual - 1)
            supabase.table("productos").update({"stock": nuevo_stock}).eq("id", producto_id).execute()

        return redirect(url_for("catalogo_publico", encargo_exito=1))

    except Exception as e:
        return f"""
            <div style="padding: 30px; font-family: sans-serif; background: #FEF2F2; color: #991B1B; border-radius: 8px; max-width: 600px; margin: 40px auto;">
                <h2>Aviso de Supabase:</h2>
                <p><strong>Detalle:</strong> {e}</p>
                <a href="/" style="display:inline-block; margin-top: 15px; background: #4F46E5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px;">Volver al Catálogo</a>
            </div>
        """

# =========================================================
# PANEL ADMIN - INICIO
# =========================================================
@app.route("/admin")
@login_required
def admin_index():
    content = """
        <div class="header-title">
            <h1>Panel de Administración</h1>
            <p>Bienvenido al centro de gestión de tu catálogo digital.</p>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 28px;">
            <a href="/pedidos" style="text-decoration:none;">
                <div style="background:white; padding:24px; border-radius:12px; border:1px solid #E2E8F0;">
                    <h3 style="color:#0F172A;">Encargos / Pedidos</h3>
                    <p style="color:#64748B; font-size:0.85rem;">Solicitudes recibidas</p>
                </div>
            </a>
            <a href="/productos" style="text-decoration:none;">
                <div style="background:white; padding:24px; border-radius:12px; border:1px solid #E2E8F0;">
                    <h3 style="color:#0F172A;">Productos</h3>
                    <p style="color:#64748B; font-size:0.85rem;">Administrar prendas y stock</p>
                </div>
            </a>
        </div>
    """
    return render_template_string(ADMIN_BASE_TEMPLATE.replace("{% block content %}{% endblock %}", content))

# =========================================================
# PANEL ADMIN - VER PEDIDOS
# =========================================================
@app.route("/pedidos")
@login_required
def ver_pedidos():
    pedidos = []
    productos_dict = {}
    
    try:
        res_pedidos = supabase.table("pedidos").select("*").execute()
        pedidos = res_pedidos.data if res_pedidos.data else []
        
        res_prod = supabase.table("productos").select("id, nombre").execute()
        if res_prod.data:
            for p in res_prod.data:
                productos_dict[str(p.get("id"))] = p.get("nombre", "Prenda Desconocida")
    except Exception as e:
        pass

    rows = ""
    for ped in pedidos:
        p_id = str(ped.get('producto_id', ''))
        nombre_prenda = productos_dict.get(p_id, 'Prenda no especificada')
        
        rows += f"""
        <tr>
            <td><strong>#{ped.get('id')}</strong></td>
            <td>{ped.get('cliente') or 'Cliente'}</td>
            <td><strong style="color: #4F46E5;">{nombre_prenda}</strong></td>
            <td><a href="https://wa.me/{ped.get('telefono')}" target="_blank" style="color:#25D366; font-weight:700; text-decoration:none;"><i class="fa-brands fa-whatsapp"></i> {ped.get('telefono')}</a></td>
            <td>{ped.get('notas') or 'Sin notas'}</td>
            <td><span style="background:#FEF3C7; color:#92400E; padding:4px 10px; border-radius:99px; font-size:0.75rem; font-weight:700;">{ped.get('estado') or 'Pendiente'}</span></td>
        </tr>
        """

    content = f"""
        <div class="header-title">
            <h1>Encargos / Solicitudes Recibidas</h1>
            <p>Lista de clientes que encargaron ropa desde la web.</p>
        </div>
        <div class="table-box">
            <table>
                <thead>
                    <tr><th>ID</th><th>Cliente</th><th>Prenda Encargada</th><th>WhatsApp</th><th>Notas / Talla</th><th>Estado</th></tr>
                </thead>
                <tbody>
                    {rows if rows else '<tr><td colspan="6">Aún no hay encargos registrados.</td></tr>'}
                </tbody>
            </table>
        </div>
    """
    return render_template_string(ADMIN_BASE_TEMPLATE.replace("{% block content %}{% endblock %}", content))

# =========================================================
# PANEL ADMIN - VER PRODUCTOS
# =========================================================
@app.route("/productos")
@login_required
def ver_productos():
    productos = []
    try:
        res = supabase.table("productos").select("*").execute()
        productos = res.data if res.data else []
    except Exception as e:
        pass

    rows = ""
    for p in productos:
        img_url = p.get('imagen_url') or p.get('imagen') or "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=500"
        stock_cant = p.get('stock') if p.get('stock') is not None else 1
        status_stock = f'<span style="color:#16A34A; font-weight:700;">{stock_cant} pzas</span>' if stock_cant > 0 else '<span style="color:#EF4444; font-weight:700;">AGOTADO (0)</span>'

        rows += f"""
        <tr>
            <td><strong>#{p.get('id')}</strong></td>
            <td><img src="{img_url}" class="img-preview-thumb"></td>
            <td>{p.get('nombre')}</td>
            <td><strong>${p.get('precio')} MXN</strong></td>
            <td>{status_stock}</td>
            <td>
                <a href="/editar/{p.get('id')}" style="color: #4F46E5; text-decoration: none; font-weight: 600; margin-right: 12px;"><i class="fa-solid fa-pen"></i> Editar</a>
                <form method="POST" action="/eliminar/{p.get('id')}" style="display:inline;">
                    <button type="submit" style="background:none; border:none; color: #EF4444; cursor:pointer; font-weight:600;" onclick="return confirm('¿Eliminar esta prenda?');"><i class="fa-solid fa-trash"></i> Eliminar</button>
                </form>
            </td>
        </tr>
        """

    content = f"""
        <div class="header-title">
            <h1>Productos en Inventario</h1>
            <p>Gestiona la ropa, fotos y piezas en existencia.</p>
        </div>
        <div class="table-box">
            <table>
                <thead>
                    <tr><th>ID</th><th>Foto</th><th>Prenda</th><th>Precio</th><th>Stock Disponible</th><th>Acciones</th></tr>
                </thead>
                <tbody>
                    {rows if rows else '<tr><td colspan="6">No hay productos registrados.</td></tr>'}
                </tbody>
            </table>
        </div>
    """
    return render_template_string(ADMIN_BASE_TEMPLATE.replace("{% block content %}{% endblock %}", content))

if __name__ == '__main__':
    app.run(debug=True)
