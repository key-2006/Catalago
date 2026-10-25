from flask import Flask, request, render_template_string, redirect, url_for, session
from functools import wraps
from supabase import create_client, Client
import base64

app = Flask(__name__)
app.secret_key = "clave_secreta_multiusuario_tiendas_123"

# Conexión directa con Supabase
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

def obtener_sidebar_admin(es_superadmin=False):
    extra_menu = ""
    if es_superadmin:
        extra_menu = '<a href="/admin/tienda/nueva" class="nav-btn" style="background: rgba(30, 58, 138, 0.2); color: #93C5FD;"><i class="fa-solid fa-plus-circle"></i> Registrar Tienda</a>'
    
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel de Control - Catálogo Digital</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <!-- Librería Cropper.js para recortar y editar fotos -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>
        <style>
            :root {{ --sidebar-bg: #18181B; --sidebar-hover: #27272A; --primary: #1E3A8A; --primary-hover: #1D4ED8; --bg: #F4F4F5; --surface: #FFFFFF; --text-main: #18181B; --text-muted: #71717A; --border: #E4E4E7; --danger: #EF4444; --radius: 8px; }}
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }}
            body {{ display: flex; min-height: 100vh; background-color: var(--bg); color: var(--text-main); }}
            .sidebar {{ width: 260px; background-color: var(--sidebar-bg); padding: 24px 16px; color: #FAFAFA; display: flex; flex-direction: column; gap: 6px; }}
            .brand {{ display: flex; align-items: center; gap: 12px; padding: 0 12px 20px 12px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 12px; }}
            .brand i {{ font-size: 1.5rem; color: #93C5FD; }}
            .brand h2 {{ font-size: 1.1rem; font-weight: 700; }}
            .brand p {{ font-size: 0.75rem; color: #A1A1AA; text-transform: uppercase; }}
            .nav-btn {{ display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 6px; color: #A1A1AA; text-decoration: none; font-weight: 600; font-size: 0.9rem; transition: all 0.2s; }}
            .nav-btn:hover, .nav-btn.active {{ background-color: var(--sidebar-hover); color: #FFFFFF; }}
            .nav-btn i {{ font-size: 1.1rem; width: 20px; text-align: center; }}
            .nav-btn.logout-link {{ margin-top: auto; background: rgba(239, 68, 68, 0.15); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.2); }}
            .nav-btn.logout-link:hover {{ background: var(--danger); color: white; }}
            .main-content {{ flex: 1; padding: 32px; overflow-y: auto; }}
            .header-title {{ margin-bottom: 24px; }}
            .header-title h1 {{ font-size: 1.75rem; font-weight: 800; color: var(--text-main); }}
            .table-box {{ background: var(--surface); padding: 24px; border-radius: var(--radius); border: 1px solid var(--border); box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
            table {{ width: 100%; border-collapse: collapse; text-align: left; }}
            th {{ padding: 12px 16px; background: #FAFAFA; color: var(--text-muted); font-size: 0.8rem; font-weight: 700; text-transform: uppercase; border-bottom: 1px solid var(--border); }}
            td {{ padding: 16px; border-bottom: 1px solid var(--border); font-size: 0.9rem; vertical-align: middle; }}
            .img-preview-thumb {{ width: 50px; height: 50px; object-fit: cover; border-radius: 6px; border: 1px solid var(--border); }}
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
            <a href="/pedidos" class="nav-btn"><i class="fa-solid fa-receipt"></i> Encargos / Pedidos</a>
            <a href="/productos" class="nav-btn"><i class="fa-solid fa-box-open"></i> Productos</a>
            <a href="/admin/ver-catalogo" class="nav-btn" target="_blank" style="background: rgba(16, 185, 129, 0.15); color: #6EE7B7;"><i class="fa-solid fa-globe"></i> Ver mi Catálogo</a>
            {extra_menu}
            <a href="/logout" class="nav-btn logout-link"><i class="fa-solid fa-right-from-bracket"></i> Cerrar Sesión</a>
        </div>
        <div class="main-content">
            {{% block content %}{% endblock %}}
        </div>
    </body>
    </html>
    """

@app.route("/")
def inicio_raiz():
    return redirect(url_for("login"))

@app.route("/tienda/<slug>")
def catalogo_tienda(slug):
    if not supabase:
        return "<h3>Error de configuración en Supabase.</h3>", 500

    try:
        res_tienda = supabase.table("tiendas").select("*").eq("slug", slug).execute()
        
        if not res_tienda.data:
            supabase.table("tiendas").insert({
                "id": 1,
                "nombre": "Vibe Apparel",
                "slug": slug,
                "subscripcion_activa": True
            }).execute()
            res_tienda = supabase.table("tiendas").select("*").eq("slug", slug).execute()

        tienda = res_tienda.data[0]
        tienda_id = tienda.get("id")
        
        if not tienda.get("subscripcion_activa", True):
            return render_template_string(PLANTILLA_SUSPENDIDO)

        res_cat = supabase.table("categorias").select("*").eq("tienda_id", tienda_id).execute()
        categorias = res_cat.data if res_cat.data else []
        
        msg_exito = request.args.get("encargo_exito")
        
        res_prod = supabase.table("productos").select("*").eq("tienda_id", tienda_id).execute()
        productos = res_prod.data if res_prod.data else []

    except Exception as e:
        return f"<div style='padding:40px; font-family:sans-serif;'><h2>Error al cargar la tienda:</h2><p>{e}</p></div>", 500

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
        prods_de_cat = productos_por_cat.get(c_id, [])
        
        if not prods_de_cat:
            continue
            
        cards_html = ""
        for p in prods_de_cat:
            img_url = p.get('imagen_url') or p.get('imagen') or "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=500"
            stock_cant = p.get('stock') if p.get('stock') is not None else 1
            
            if stock_cant <= 0:
                badge_stock = '<span class="badge-stock stock-out">Agotado</span>'
                overlay_agotado = '<div class="sold-out-overlay">AGOTADO</div>'
                btn_html = f'<button class="btn-encargar btn-disabled" disabled><i class="fa-solid fa-ban"></i> Prenda Agotada</button>'
                img_class = "img-grayscale"
            else:
                badge_stock = f'<span class="badge-stock stock-in">Disponibles: {stock_cant}</span>'
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
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span class="category-badge">{c_nombre}</span>
                        {badge_stock}
                    </div>
                    <h3 class="product-title">{p.get('nombre')}</h3>
                    <div class="price-row" style="margin-bottom:12px;">
                        <span class="price">${p.get('precio')} MXN</span>
                    </div>
                    {btn_html}
                </div>
            </div>
            """
        
        secciones_html += f"""
        <div class="category-section">
            <h2 class="category-section-title">{c_nombre}</h2>
            <div class="products-grid">
                {cards_html}
            </div>
        </div>
        """

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{tienda.get('nombre')} - Catálogo Exclusivo</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root {{ --primary: #1E3A8A; --primary-hover: #1D4ED8; --bg: #FAFAFA; --surface: #FFFFFF; --text: #18181B; --muted: #71717A; --border: #E4E4E7; }}
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }}
            body {{ background: var(--bg); color: var(--text); }}
            nav {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 1.2rem 2.5rem; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 10; }}
            .logo {{ font-size: 1.2rem; font-weight: 800; color: var(--text); text-decoration: none; display: flex; align-items: center; gap: 8px; letter-spacing: -0.5px; }}
            .hero {{ background: #18181B; color: white; padding: 3rem 1.5rem; text-align: center; margin: 0 auto; }}
            .hero h1 {{ font-size: 2rem; font-weight: 800; margin-bottom: 8px; letter-spacing: -0.5px; }}
            .hero p {{ color: #A1A1AA; font-size: 0.95rem; }}
            .container-main {{ max-width: 1200px; margin: 2.5rem auto; padding: 0 1.5rem; }}
            .category-section {{ margin-bottom: 3rem; }}
            .category-section-title {{ font-size: 1.25rem; font-weight: 700; color: var(--text); margin-bottom: 1.2rem; border-bottom: 1px solid var(--border); padding-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }}
            .products-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1.5rem; }}
            .product-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; position: relative; transition: transform 0.2s; }}
            .product-card:hover {{ transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.04); }}
            .img-wrapper {{ position: relative; width: 100%; height: 280px; background: #F4F4F5; overflow: hidden; }}
            .img-wrapper img {{ width: 100%; height: 100%; object-fit: cover; }}
            .card-content {{ padding: 1.2rem; display: flex; flex-direction: column; flex: 1; }}
            .category-badge {{ font-size: 0.7rem; color: var(--muted); font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
            .badge-stock {{ font-size: 0.75rem; font-weight: 600; color: #047857; background: #ECFDF5; padding: 2px 8px; border-radius: 4px; }}
            .stock-out {{ background: #FEF2F2; color: #B91C1C; }}
            .product-title {{ font-size: 1.05rem; margin: 6px 0 4px; font-weight: 700; color: var(--text); }}
            .price {{ font-size: 1.15rem; font-weight: 800; color: var(--text); }}
            .btn-encargar {{ display: flex; align-items: center; justify-content: center; gap: 8px; background: var(--primary); color: white; border: none; padding: 12px; border-radius: 6px; font-weight: 600; cursor: pointer; width: 100%; transition: background 0.2s; }}
            .btn-encargar:hover {{ background: var(--primary-hover); }}
            .btn-disabled {{ background: #E4E4E7; color: #A1A1AA; cursor: not-allowed; }}
            .modal-overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); backdrop-filter: blur(2px); display: none; align-items: center; justify-content: center; z-index: 100; }}
            .modal-box {{ background: white; padding: 30px; border-radius: 12px; max-width: 450px; width: 90%; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); }}
            .alert-toast {{ background: #065F46; color: white; padding: 12px; border-radius: 6px; max-width: 1200px; margin: 1.5rem auto 0; text-align: center; font-weight: 600; }}
        </style>
    </head>
    <body>
        <nav>
            <a href="/tienda/{slug}" class="logo"><i class="fa-solid fa-gem"></i> {tienda.get('nombre')}</a>
            <a href="/login" style="color: var(--muted); text-decoration: none; font-weight: 600; font-size: 0.9rem;"><i class="fa-solid fa-lock"></i> Acceso Admin</a>
        </nav>

        <section class="hero">
            <h1>Colección Exclusiva</h1>
            <p>Selección de prendas seleccionadas para {tienda.get('nombre')}.</p>
        </section>

        {'<div class="alert-toast">¡Tu encargo ha sido registrado correctamente! Nos pondremos en contacto contigo.</div>' if msg_exito else ''}

        <div class="container-main">
            {secciones_html if secciones_html else '<p style="text-align: center; color: var(--muted); padding: 4rem;">No hay prendas disponibles en este momento.</p>'}
        </div>

        <div class="modal-overlay" id="modalEncargo">
            <div class="modal-box">
                <h3 style="font-size: 1.25rem; font-weight: 800; margin-bottom: 4px; color: var(--text);">Solicitar Encargo</h3>
                <p id="modalPrendaNombre" style="color: var(--primary); font-weight: 700; margin-bottom: 20px; font-size: 0.95rem;"></p>
                <form action="/hacer-encargo" method="POST">
                    <input type="hidden" name="tienda_id" value="{tienda_id}">
                    <input type="hidden" name="slug" value="{slug}">
                    <input type="hidden" name="producto_id" id="modalProductoId">
                    
                    <label style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: var(--muted);">Nombre Completo</label>
                    <input type="text" name="nombre_cliente" style="width:100%; padding:10px 12px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px; font-size:0.95rem;" required>
                    
                    <label style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: var(--muted);">Teléfono / WhatsApp</label>
                    <input type="tel" name="telefono" style="width:100%; padding:10px 12px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px; font-size:0.95rem;" required>
                    
                    <label style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: var(--muted);">Método de Pago</label>
                    <select name="metodo_pago" style="width:100%; padding:10px 12px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px; font-size:0.95rem; background:white;" required>
                        <option value="Efectivo al Entregar">Efectivo al Entregar</option>
                        <option value="Transferencia SPEI">Transferencia SPEI</option>
                        <option value="Tarjeta de Débito/Crédito">Tarjeta de Débito / Crédito</option>
                    </select>

                    <label style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: var(--muted);">Notas o Talla Deseada</label>
                    <textarea name="notas" rows="3" style="width:100%; padding:10px 12px; margin:6px 0 20px; border:1px solid var(--border); border-radius:6px; font-size:0.95rem; resize:none;"></textarea>
                    
                    <div style="display: flex; gap: 10px;">
                        <button type="submit" style="flex: 1; background: var(--primary); color: white; border: none; padding: 12px; border-radius: 6px; font-weight: 700; cursor: pointer;">Confirmar</button>
                        <button type="button" onclick="cerrarModal()" style="background: #F4F4F5; color: var(--text); border: none; padding: 12px 16px; border-radius: 6px; font-weight: 700; cursor: pointer;">Cancelar</button>
                    </div>
                </form>
            </div>
        </div>

        <script>
            function abrirModal(id, nombre, precio) {{
                document.getElementById('modalProductoId').value = id;
                document.getElementById('modalPrendaNombre').innerText = nombre + " — $" + precio + " MXN";
                document.getElementById('modalEncargo').style.display = 'flex';
            }}
            function cerrarModal() {{
                document.getElementById('modalEncargo').style.display = 'none';
            }}
        </script>
    </body>
    </html>
    """)

@app.route("/hacer-encargo", methods=["POST"])
def hacer_encargo():
    tienda_id = request.form.get("tienda_id")
    slug = request.form.get("slug")
    producto_id = request.form.get("producto_id")
    nombre_cliente = request.form.get("nombre_cliente")
    telefono = request.form.get("telefono")
    metodo_pago = request.form.get("metodo_pago")
    notas = request.form.get("notas")
    
    try:
        supabase.table("pedidos").insert({
            "tienda_id": tienda_id,
            "cliente": nombre_cliente,
            "telefono": telefono,
            "metodo_pago": metodo_pago,
            "notas": notas,
            "producto_id": producto_id,
            "estado": "Pendiente"
        }).execute()
        
        res_prod = supabase.table("productos").select("stock").eq("id", producto_id).execute()
        if res_prod.data:
            stock_actual = res_prod.data[0].get('stock') if res_prod.data[0].get('stock') is not None else 1
            nuevo_stock = max(0, stock_actual - 1)
            supabase.table("productos").update({"stock": nuevo_stock}).eq("id", producto_id).execute()

        return redirect(url_for("catalogo_tienda", slug=slug, encargo_exito=1))
    except Exception as e:
        return f"Error al procesar el encargo: {e}"

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user_input = request.form.get("username")
        pass_input = request.form.get("password")
        
        if user_input == "super_master" and pass_input == "master2026":
            session["logged_in"] = True
            session["is_superadmin"] = True
            return redirect(url_for("super_admin_panel"))
        
        try:
            res = supabase.table("administradores").select("*").eq("username", user_input).execute()
            
            if res.data and len(res.data) > 0:
                admin = res.data[0]
                if admin.get("password") == pass_input:
                    session["logged_in"] = True
                    session["tienda_id"] = admin.get("tienda_id")
                    session["username"] = admin.get("username")
                    session.pop("is_superadmin", None)
                    return redirect(url_for("admin_index"))
            
            error = "Usuario o contraseña incorrectos."
        except Exception as e:
            error = f"Error al validar credenciales: {e}"

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Acceso Admin</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
            body { background: #18181B; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
            .login-card { background: #27272A; padding: 32px; border-radius: 12px; border: 1px solid #3F3F46; width: 100%; max-width: 400px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
            .login-card h2 { color: #FAFAFA; font-size: 1.4rem; font-weight: 700; margin-bottom: 6px; text-align: center; }
            p.sub { color: #A1A1AA; font-size: 0.85rem; text-align: center; margin-bottom: 24px; }
            label { font-size: 0.8rem; font-weight: 700; color: #D4D4D8; text-transform: uppercase; }
            input { width: 100%; padding: 12px; margin: 6px 0 16px; background: #18181B; border: 1px solid #3F3F46; color: white; border-radius: 6px; }
            button { width: 100%; padding: 12px; background: #1E3A8A; color: white; border: none; border-radius: 6px; font-weight: 700; cursor: pointer; transition: background 0.2s; }
            button:hover { background: #1D4ED8; }
        </style>
    </head>
    <body>
        <div class="login-card">
            <h2>Panel de Acceso</h2>
            <p class="sub">Gestión interna del local o plataforma</p>
            {% if error %}<p style="color:#FCA5A5; text-align:center; margin-bottom:12px; font-size:0.85rem;">{{ error }}</p>{% endif %}
            <form method="POST">
                <label>Usuario</label>
                <input type="text" name="username" required>
                <label>Contraseña</label>
                <input type="password" name="password" required>
                <button type="submit">Ingresar</button>
            </form>
        </div>
    </body>
    </html>
    """, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/super-admin")
def super_admin_panel():
    if not session.get("logged_in") or not session.get("is_superadmin"):
        return redirect(url_for("login"))
    
    tiendas = []
    try:
        res = supabase.table("tiendas").select("*").order("id").execute()
        tiendas = res.data if res.data else []
    except Exception as e:
        pass

    rows = ""
    for t in tiendas:
        t_id = t.get('id')
        t_nombre = t.get('nombre')
        t_slug = t.get('slug')
        activa = t.get('subscripcion_activa', True)
        
        status_badge = '<span style="background:#ECFDF5; color:#047857; padding:4px 10px; border-radius:99px; font-weight:600; font-size:0.8rem;">Al Corriente (Activa)</span>' if activa else '<span style="background:#FEF2F2; color:#B91C1C; padding:4px 10px; border-radius:99px; font-weight:600; font-size:0.8rem;">Suspendida (Pendiente de Pago)</span>'
        btn_accion = f'<a href="/super-admin/cambiar-estatus/{t_id}" style="background:{"#B91C1C" if activa else "#047857"}; color:white; padding:6px 12px; border-radius:4px; text-decoration:none; font-weight:600; font-size:0.85rem;">{"Suspender" if activa else "Activar"}</a>'
        
        rows += f"""
        <tr>
            <td><strong>#{t_id}</strong></td>
            <td><strong>{t_nombre}</strong></td>
            <td><code>/tienda/{t_slug}</code></td>
            <td>{status_badge}</td>
            <td>{btn_accion}</td>
        </tr>
        """

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Control Maestro de Tiendas - Plataforma</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }}
            body {{ background: #F4F4F5; color: #18181B; padding: 40px; }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }}
            .table-box {{ background: white; padding: 24px; border-radius: 8px; border: 1px solid #E4E4E7; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
            table {{ width: 100%; border-collapse: collapse; text-align: left; }}
            th {{ padding: 12px 16px; background: #FAFAFA; color: #71717A; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; border-bottom: 1px solid #E4E4E7; }}
            td {{ padding: 16px; border-bottom: 1px solid #E4E4E7; font-size: 0.9rem; vertical-align: middle; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1 style="font-size: 1.8rem; font-weight: 800;"><i class="fa-solid fa-shield-halved" style="color:#1E3A8A;"></i> Control Maestro de Tiendas</h1>
                    <p style="color: #71717A; font-size: 0.9rem;">Monitorea el estatus de suscripciones y pagos de todos los locales registrados.</p>
                </div>
                <a href="/logout" style="background:#EF4444; color:white; padding:10px 16px; border-radius:6px; text-decoration:none; font-weight:600; font-size:0.9rem;"><i class="fa-solid fa-right-from-bracket"></i> Cerrar Sesión</a>
            </div>
            
            <div class="table-box">
                <table>
                    <thead><tr><th>ID</th><th>Nombre de la Tienda</th><th>URL / Slug</th><th>Estatus de Suscripción</th><th>Acciones de Pago</th></tr></thead>
                    <tbody>{rows if rows else '<tr><td colspan="5" style="text-align:center; color:#71717A;">No hay tiendas registradas.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """)

@app.route("/super-admin/cambiar-estatus/<int:id>")
def cambiar_estatus_tienda(id):
    if not session.get("logged_in") or not session.get("is_superadmin"):
        return redirect(url_for("login"))
    
    try:
        res = supabase.table("tiendas").select("subscripcion_activa").eq("id", id).execute()
        if res.data:
            estado_actual = res.data[0].get("subscripcion_activa", True)
            nuevo_estado = not estado_actual
            supabase.table("tiendas").update({"subscripcion_activa": nuevo_estado}).eq("id", id).execute()
    except Exception as e:
        pass
    
    return redirect(url_for("super_admin_panel"))

@app.route("/admin")
@login_required
def admin_index():
    tienda_id = session.get("tienda_id")
    nombre_tienda = "Mi Local"
    try:
        res = supabase.table("tiendas").select("nombre").eq("id", tienda_id).execute()
        if res.data:
            nombre_tienda = res.data[0].get("nombre")
    except:
        pass

    content = f"""
        <div class="header-title">
            <h1>Panel Administrativo</h1>
            <p style="color: var(--text-muted); font-size: 0.95rem;">Bienvenido a la administración de {nombre_tienda}.</p>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; max-width: 700px;">
            <a href="/pedidos" style="text-decoration:none;">
                <div style="background:white; padding:24px; border-radius:8px; border:1px solid var(--border); transition: border-color 0.2s;">
                    <h3 style="color:var(--text-main); font-size:1.1rem; display:flex; align-items:center; gap:10px;"><i class="fa-solid fa-receipt" style="color:var(--primary);"></i> Encargos</h3>
                    <p style="color:var(--text-muted); font-size:0.85rem; margin-top:6px;">Revisa las solicitudes de compra.</p>
                </div>
            </a>
            <a href="/productos" style="text-decoration:none;">
                <div style="background:white; padding:24px; border-radius:8px; border:1px solid var(--border); transition: border-color 0.2s;">
                    <h3 style="color:var(--text-main); font-size:1.1rem; display:flex; align-items:center; gap:10px;"><i class="fa-solid fa-box-open" style="color:var(--primary);"></i> Productos</h3>
                    <p style="color:var(--text-muted); font-size:0.85rem; margin-top:6px;">Gestiona el catálogo e inventario.</p>
                </div>
            </a>
        </div>
    """
    is_super = session.get("is_superadmin", False)
    return render_template_string(obtener_sidebar_admin(es_superadmin=is_super).replace("{% block content %}{% endblock %}", content))

@app.route("/admin/ver-catalogo")
@login_required
def ver_catalogo_admin():
    tienda_id = session.get("tienda_id")
    try:
        res = supabase.table("tiendas").select("slug").eq("id", tienda_id).execute()
        if res.data:
            slug = res.data[0].get("slug")
            return redirect(url_for("catalogo_tienda", slug=slug))
    except:
        pass
    return redirect(url_for("admin_index"))

@app.route("/admin/tienda/nueva", methods=["GET", "POST"])
def nueva_tienda():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
        
    error = None
    if request.method == "POST":
        nombre_tienda = request.form.get("nombre")
        slug_tienda = request.form.get("slug")
        admin_user = request.form.get("admin_user")
        admin_pass = request.form.get("admin_pass")
        
        try:
            res_t = supabase.table("tiendas").insert({
                "nombre": nombre_tienda,
                "slug": slug_tienda,
                "subscripcion_activa": True
            }).execute()
            
            if res_t.data:
                nueva_tienda_id = res_t.data[0].get("id")
                
                supabase.table("administradores").insert({
                    "username": admin_user,
                    "password": admin_pass,
                    "tienda_id": nueva_tienda_id
                }).execute()
                
                return redirect(url_for("catalogo_tienda", slug=slug_tienda))
            else:
                error = "No se pudo crear la tienda en la base de datos."
        except Exception as e:
            error = f"Error al registrar: {e}"

    content = f"""
        <div class="header-title"><h1>Registrar Nueva Tienda</h1></div>
        <div class="table-box" style="max-width: 600px;">
            {'<p style="color:red; margin-bottom:12px; font-size:0.85rem;">' + error + '</p>' if error else ''}
            <form method="POST">
                <label style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Nombre Comercial del Local</label>
                <input type="text" name="nombre" placeholder="Ej. Urban Style" style="width:100%; padding:10px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px;" required>
                
                <label style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Identificador URL (Slug sin espacios)</label>
                <input type="text" name="slug" placeholder="Ej. urban-style" style="width:100%; padding:10px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px;" required>
                
                <label style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Usuario Administrador</label>
                <input type="text" name="admin_user" placeholder="Ej. urban_admin" style="width:100%; padding:10px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px;" required>
                
                <label style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Contraseña del Administrador</label>
                <input type="password" name="admin_pass" style="width:100%; padding:10px; margin:6px 0 20px; border:1px solid var(--border); border-radius:6px;" required>
                
                <div style="display:flex; gap:10px;">
                    <button type="submit" style="background:var(--primary); color:white; border:none; padding:10px 20px; border-radius:6px; font-weight:700; cursor:pointer;">Crear Tienda e Ir al Catálogo</button>
                    <a href="/admin" style="background:#F4F4F5; color:var(--text-main); padding:10px 20px; border-radius:6px; text-decoration:none; font-weight:700; display:inline-block;">Cancelar</a>
                </div>
            </form>
        </div>
    """
    is_super = session.get("is_superadmin", False)
    return render_template_string(obtener_sidebar_admin(es_superadmin=is_super).replace("{% block content %}{% endblock %}", content))

@app.route("/pedidos")
@login_required
def ver_pedidos():
    tienda_id = session.get("tienda_id")
    pedidos = []
    try:
        res = supabase.table("pedidos").select("*").eq("tienda_id", tienda_id).execute()
        pedidos = res.data if res.data else []
    except Exception as e:
        pass

    rows = ""
    for ped in pedidos:
        rows += f"""
        <tr>
            <td><strong>#{ped.get('id')}</strong></td>
            <td>{ped.get('cliente') or 'Cliente'}</td>
            <td><a href="https://wa.me/{ped.get('telefono')}" target="_blank" style="color:#047857; font-weight:700; text-decoration:none;"><i class="fa-brands fa-whatsapp"></i> {ped.get('telefono')}</a></td>
            <td><span style="background:#F4F4F5; color:#18181B; padding:4px 8px; border-radius:4px; font-weight:600; font-size:0.85rem;">{ped.get('metodo_pago') or 'No especificado'}</span></td>
            <td>{ped.get('notas') or 'Sin notas'}</td>
            <td><span style="background:#FEF3C7; color:#B45309; padding:4px 10px; border-radius:99px; font-size:0.8rem; font-weight:600;">{ped.get('estado') or 'Pendiente'}</span></td>
        </tr>
        """

    content = f"""
        <div class="header-title"><h1>Encargos Recibidos</h1></div>
        <div class="table-box">
            <table>
                <thead><tr><th>ID</th><th>Cliente</th><th>WhatsApp</th><th>Método de Pago</th><th>Notas</th><th>Estado</th></tr></thead>
                <tbody>{rows if rows else '<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No hay encargos registrados.</td></tr>'}</tbody>
            </table>
        </div>
    """
    is_super = session.get("is_superadmin", False)
    return render_template_string(obtener_sidebar_admin(es_superadmin=is_super).replace("{% block content %}{% endblock %}", content))

@app.route("/productos")
@login_required
def ver_productos():
    tienda_id = session.get("tienda_id")
    productos = []
    try:
        res = supabase.table("productos").select("*").eq("tienda_id", tienda_id).execute()
        productos = res.data if res.data else []
    except Exception as e:
        pass

    rows = ""
    for p in productos:
        img_url = p.get('imagen_url') or p.get('imagen') or "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=500"
        rows += f"""
        <tr>
            <td><strong>#{p.get('id')}</strong></td>
            <td><img src="{img_url}" class="img-preview-thumb"></td>
            <td>{p.get('nombre')}</td>
            <td><strong>${p.get('precio')} MXN</strong></td>
            <td>{p.get('stock', 0)} pzas</td>
            <td>
                <a href="/admin/producto/editar/{p.get('id')}" style="background:#F4F4F5; color:#18181B; padding:6px 12px; border-radius:4px; text-decoration:none; font-weight:600; font-size:0.85rem; margin-right:4px;"><i class="fa-solid fa-pen"></i> Editar</a>
                <a href="/admin/producto/eliminar/{p.get('id')}" onclick="return confirm('¿Estás seguro de eliminar este producto?');" style="background:#FEF2F2; color:#B91C1C; padding:6px 12px; border-radius:4px; text-decoration:none; font-weight:600; font-size:0.85rem;"><i class="fa-solid fa-trash"></i> Borrar</a>
            </td>
        </tr>
        """

    content = f"""
        <div class="header-title" style="display:flex; justify-content:space-between; align-items:center;">
            <h1>Inventario de Productos</h1>
            <a href="/admin/producto/nuevo" style="background:var(--primary); color:white; padding:10px 16px; border-radius:6px; text-decoration:none; font-weight:600; font-size:0.9rem;"><i class="fa-solid fa-plus"></i> Añadir Prenda</a>
        </div>
        <div class="table-box">
            <table>
                <thead><tr><th>ID</th><th>Foto</th><th>Prenda</th><th>Precio</th><th>Stock</th><th>Acciones</th></tr></thead>
                <tbody>{rows if rows else '<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No hay productos registrados.</td></tr>'}</tbody>
            </table>
        </div>
    """
    is_super = session.get("is_superadmin", False)
    return render_template_string(obtener_sidebar_admin(es_superadmin=is_super).replace("{% block content %}{% endblock %}", content))

@app.route("/admin/producto/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_producto():
    tienda_id = session.get("tienda_id")
    error = None
    
    categorias = []
    try:
        res_cat = supabase.table("categorias").select("*").eq("tienda_id", tienda_id).execute()
        categorias = res_cat.data if res_cat.data else []
    except:
        pass

    if request.method == "POST":
        nombre = request.form.get("nombre")
        precio = request.form.get("precio")
        stock = request.form.get("stock")
        categoria_id = request.form.get("categoria_id")
        
        # Aquí recibimos la imagen ya recortada enviada en Base64 desde el editor visual
        imagen_url = request.form.get("imagen_recortada")
        
        try:
            supabase.table("productos").insert({
                "tienda_id": tienda_id,
                "nombre": nombre,
                "precio": float(precio) if precio else 0,
                "stock": int(stock) if stock else 1,
                "categoria_id": int(categoria_id) if categoria_id else None,
                "imagen_url": imagen_url
            }).execute()
            return redirect(url_for("ver_productos"))
        except Exception as e:
            error = f"Error al guardar: {e}"

    options_cat = "".join([f"<option value='{c.get('id')}'>{c.get('nombre')}</option>" for c in categorias])
    
    content = f"""
        <div class="header-title"><h1>Nuevo Producto</h1></div>
        <div class="table-box" style="max-width: 600px;">
            {'<p style="color:red; margin-bottom:12px; font-size:0.85rem;">' + error + '</p>' if error else ''}
            <form method="POST" id="formProducto">
                <input type="hidden" name="imagen_recortada" id="imagen_recortada">

                <label style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Nombre de la Prenda</label>
                <input type="text" name="nombre" style="width:100%; padding:10px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px;" required>
                
                <label style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Precio (MXN)</label>
                <input type="number" step="0.01" name="precio" style="width:100%; padding:10px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px;" required>
                
                <label style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Stock Inicial</label>
                <input type="number" name="stock" value="10" style="width:100%; padding:10px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px;" required>
                
                <label style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Categoría</label>
                <select name="categoria_id" style="width:100%; padding:10px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px; background:white;">
                    {options_cat}
                </select>
                
                <label style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Fotografía (Toma o Selecciona)</label>
                <input type="file" id="inputFoto" accept="image/*" style="width:100%; padding:8px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px;" required>

                <!-- Contenedor del Editor / Recortador de Imagen -->
                <div id="editorContainer" style="display:none; margin-bottom:20px; background:#18181B; padding:15px; border-radius:8px; text-align:center;">
                    <div style="max-height: 350px; overflow: hidden; margin-bottom: 12px;">
                        <img id="imagenParaRecortar" style="max-width: 100%;">
                    </div>
                    <div style="display:flex; gap:10px; justify-content:center;">
                        <button type="button" onclick="girarImagen()" style="background:#3F3F46; color:white; border:none; padding:8px 14px; border-radius:4px; cursor:pointer; font-weight:600;"><i class="fa-solid fa-rotate-right"></i> Girar</button>
                        <button type="button" onclick="confirmarRecorte()" style="background:#047857; color:white; border:none; padding:8px 16px; border-radius:4px; cursor:pointer; font-weight:600;"><i class="fa-solid fa-check"></i> Aplicar Recorte</button>
                    </div>
                </div>

                <div id="vistaPreviaBox" style="display:none; margin-bottom:20px; text-align:center;">
                    <p style="font-size:0.8rem; color:#047857; font-weight:700; margin-bottom:6px;"><i class="fa-solid fa-circle-check"></i> Imagen recortada y lista</p>
                    <img id="imgResultadoPrev" style="width:100px; height:100px; object-fit:cover; border-radius:6px; border:1px solid var(--border);">
                </div>
                
                <div style="display:flex; gap:10px;">
                    <button type="submit" id="btnGuardar" style="background:var(--primary); color:white; border:none; padding:10px 20px; border-radius:6px; font-weight:700; cursor:pointer;">Guardar Producto</button>
                    <a href="/productos" style="background:#F4F4F5; color:var(--text-main); padding:10px 20px; border-radius:6px; text-decoration:none; font-weight:700; display:inline-block;">Cancelar</a>
                </div>
            </form>
        </div>

        <script>
            let cropper = null;
            const inputFoto = document.getElementById('inputFoto');
            const editorContainer = document.getElementById('editorContainer');
            const imagenParaRecortar = document.getElementById('imagenParaRecortar');
            const vistaPreviaBox = document.getElementById('vistaPreviaBox');
            const imgResultadoPrev = document.getElementById('imgResultadoPrev');
            const inputBase64 = document.getElementById('imagen_recortada');

            inputFoto.addEventListener('change', function(e) {{
                const files = e.target.files;
                if (files && files.length > 0) {{
                    const file = files[0];
                    const reader = new FileReader();
                    reader.onload = function(event) {{
                        imagenParaRecortar.src = event.target.result;
                        editorContainer.style.display = 'block';
                        vistaPreviaBox.style.display = 'none';
                        
                        if (cropper) {{
                            cropper.destroy();
                        }}
                        cropper = new Cropper(imagenParaRecortar, {{
                            aspectRatio: 1, // Cuadrado perfecto ideal para ropa
                            viewMode: 1,
                            autoCropArea: 0.9,
                        }});
                    }};
                    reader.readAsDataURL(file);
                }}
            }});

            function girarImagen() {{
                if (cropper) {{
                    cropper.rotate(90);
                }}
            }}

            function confirmarRecorte() {{
                if (cropper) {{
                    const canvas = cropper.getCroppedCanvas({{
                        width: 600,
                        height: 600
                    }});
                    const base64String = canvas.toDataURL('image/jpeg');
                    
                    inputBase64.value = base64String;
                    imgResultadoPrev.src = base64String;
                    
                    editorContainer.style.display = 'none';
                    vistaPreviaBox.style.display = 'block';
                }}
            }}
        </script>
    """
    is_super = session.get("is_superadmin", False)
    return render_template_string(obtener_sidebar_admin(es_superadmin=is_super).replace("{% block content %}{% endblock %}", content))

@app.route("/admin/producto/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_producto(id):
    tienda_id = session.get("tienda_id")
    error = None
    
    try:
        res_prod = supabase.table("productos").select("*").eq("id", id).eq("tienda_id", tienda_id).execute()
        if not res_prod.data:
            return redirect(url_for("ver_productos"))
        producto = res_prod.data[0]
    except:
        return redirect(url_for("ver_productos"))

    categorias = []
    try:
        res_cat = supabase.table("categorias").select("*").eq("tienda_id", tienda_id).execute()
        categorias = res_cat.data if res_cat.data else []
    except:
        pass

    if request.method == "POST":
        nombre = request.form.get("nombre")
        precio = request.form.get("precio")
        stock = request.form.get("stock")
        categoria_id = request.form.get("categoria_id")
        
        nueva_imagen = request.form.get("imagen_recortada")
        if nueva_imagen and nueva_imagen != "":
            imagen_url = nueva_imagen
        else:
            imagen_url = producto.get('imagen_url') or producto.get('imagen')
        
        try:
            supabase.table("productos").update({
                "nombre": nombre,
                "precio": float(precio) if precio else 0,
                "stock": int(stock) if stock else 0,
                "categoria_id": int(categoria_id) if categoria_id else None,
                "imagen_url": imagen_url
            }).eq("id", id).eq("tienda_id", tienda_id).execute()
            return redirect(url_for("ver_productos"))
        except Exception as e:
            error = f"Error al actualizar: {e}"

    options_cat = "".join([f"<option value='{c.get('id')}' {'selected' if str(c.get('id')) == str(producto.get('categoria_id')) else ''}>{c.get('nombre')}</option>" for c in categorias])
    foto_actual = producto.get('imagen_url') or producto.get('imagen') or "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=500"
    
    content = f"""
        <div class="header-title"><h1>Editar Producto</h1></div>
        <div class="table-box" style="max-width: 600px;">
            {'<p style="color:red; margin-bottom:12px; font-size:0.85rem;">' + error + '</p>' if error else ''}
            <form method="POST">
                <input type="hidden" name="imagen_recortada" id="imagen_recortada">

                <label style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Nombre de la Prenda</label>
                <input type="text" name="nombre" value="{producto.get('nombre', '')}" style="width:100%; padding:10px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px;" required>
                
                <label style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Precio (MXN)</label>
                <input type="number" step="0.01" name="precio" value="{producto.get('precio', 0)}" style="width:100%; padding:10px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px;" required>
                
                <label style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Stock Actual</label>
                <input type="number" name="stock" value="{producto.get('stock', 0)}" style="width:100%; padding:10px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px;" required>
                
                <label style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Categoría</label>
                <select name="categoria_id" style="width:100%; padding:10px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px; background:white;">
                    {options_cat}
                </select>
                
                <label style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Fotografía Actual</label>
                <div style="margin-bottom: 12px;">
                    <img src="{foto_actual}" style="width:80px; height:80px; object-fit:cover; border-radius:6px; border:1px solid var(--border);">
                </div>

                <label style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Cambiar y Recortar Nueva Foto (Opcional)</label>
                <input type="file" id="inputFoto" accept="image/*" style="width:100%; padding:8px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px;">

                <div id="editorContainer" style="display:none; margin-bottom:20px; background:#18181B; padding:15px; border-radius:8px; text-align:center;">
                    <div style="max-height: 350px; overflow: hidden; margin-bottom: 12px;">
                        <img id="imagenParaRecortar" style="max-width: 100%;">
                    </div>
                    <div style="display:flex; gap:10px; justify-content:center;">
                        <button type="button" onclick="girarImagen()" style="background:#3F3F46; color:white; border:none; padding:8px 14px; border-radius:4px; cursor:pointer; font-weight:600;"><i class="fa-solid fa-rotate-right"></i> Girar</button>
                        <button type="button" onclick="confirmarRecorte()" style="background:#047857; color:white; border:none; padding:8px 16px; border-radius:4px; cursor:pointer; font-weight:600;"><i class="fa-solid fa-check"></i> Aplicar Recorte</button>
                    </div>
                </div>

                <div id="vistaPreviaBox" style="display:none; margin-bottom:20px; text-align:center;">
                    <p style="font-size:0.8rem; color:#047857; font-weight:700; margin-bottom:6px;"><i class="fa-solid fa-circle-check"></i> Nueva foto lista</p>
                    <img id="imgResultadoPrev" style="width:100px; height:100px; object-fit:cover; border-radius:6px; border:1px solid var(--border);">
                </div>
                
                <div style="display:flex; gap:10px;">
                    <button type="submit" style="background:var(--primary); color:white; border:none; padding:10px 20px; border-radius:6px; font-weight:700; cursor:pointer;">Actualizar</button>
                    <a href="/productos" style="background:#F4F4F5; color:var(--text-main); padding:10px 20px; border-radius:6px; text-decoration:none; font-weight:700; display:inline-block;">Cancelar</a>
                </div>
            </form>
        </div>

        <script>
            let cropper = null;
            const inputFoto = document.getElementById('inputFoto');
            const editorContainer = document.getElementById('editorContainer');
            const imagenParaRecortar = document.getElementById('imagenParaRecortar');
            const vistaPreviaBox = document.getElementById('vistaPreviaBox');
            const imgResultadoPrev = document.getElementById('imgResultadoPrev');
            const inputBase64 = document.getElementById('imagen_recortada');

            inputFoto.addEventListener('change', function(e) {{
                const files = e.target.files;
                if (files && files.length > 0) {{
                    const file = files[0];
                    const reader = new FileReader();
                    reader.onload = function(event) {{
                        imagenParaRecortar.src = event.target.result;
                        editorContainer.style.display = 'block';
                        vistaPreviaBox.style.display = 'none';
                        
                        if (cropper) {{
                            cropper.destroy();
                        }}
                        cropper = new Cropper(imagenParaRecortar, {{
                            aspectRatio: 1,
                            viewMode: 1,
                            autoCropArea: 0.9,
                        }});
                    }};
                    reader.readAsDataURL(file);
                }}
            }});

            function girarImagen() {{
                if (cropper) {{
                    cropper.rotate(90);
                }}
            }}

            function confirmarRecorte() {{
                if (cropper) {{
                    const canvas = cropper.getCroppedCanvas({{
                        width: 600,
                        height: 600
                    }});
                    const base64String = canvas.toDataURL('image/jpeg');
                    
                    inputBase64.value = base64String;
                    imgResultadoPrev.src = base64String;
                    
                    editorContainer.style.display = 'none';
                    vistaPreviaBox.style.display = 'block';
                }}
            }}
        </script>
    """
    is_super = session.get("is_superadmin", False)
    return render_template_string(obtener_sidebar_admin(es_superadmin=is_super).replace("{% block content %}{% endblock %}", content))

@app.route("/admin/producto/eliminar/<int:id>")
@login_required
def eliminar_producto(id):
    tienda_id = session.get("tienda_id")
    try:
        supabase.table("productos").delete().eq("id", id).eq("tienda_id", tienda_id).execute()
    except Exception as e:
        pass
    return redirect(url_for("ver_productos"))

if __name__ == '__main__':
    app.run(debug=True)
