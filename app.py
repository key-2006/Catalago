from flask import Flask, request, render_template_string, redirect, url_for, session
from functools import wraps
from supabase import create_client, Client
from datetime import datetime, timezone, timedelta
import base64

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

def obtener_sidebar_admin(es_superadmin=False, pedidos_pendientes=0):
    extra_menu = ""
    if es_superadmin:
        extra_menu = '<a href="/admin/tienda/nueva" class="nav-btn" style="background: rgba(30, 58, 138, 0.2); color: #93C5FD;"><i class="fa-solid fa-plus-circle"></i> Registrar Tienda</a>'
    
    badge_html = ""
    if pedidos_pendientes > 0:
        badge_html = f'<span style="background: #EF4444; color: white; padding: 2px 8px; border-radius: 99px; font-size: 0.75rem; font-weight: 700; margin-left: auto;">{pedidos_pendientes}</span>'

    plantilla_base = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel de Control - Catálogo Digital</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css">
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
            table { width: 100%; border-collapse: collapse; text-align: left; min-width: 1000px; }
            th { padding: 12px 16px; background: #FAFAFA; color: var(--text-muted); font-size: 0.8rem; font-weight: 700; text-transform: uppercase; border-bottom: 1px solid var(--border); }
            td { padding: 16px; border-bottom: 1px solid var(--border); font-size: 0.9rem; vertical-align: middle; }
            .img-preview-thumb { width: 50px; height: 50px; object-fit: cover; border-radius: 6px; border: 1px solid var(--border); }
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
            <a href="/pedidos" class="nav-btn" style="display:flex; align-items:center;"><i class="fa-solid fa-receipt"></i> Encargos PEDIDOS_BADGE</a>
            <a href="/productos" class="nav-btn"><i class="fa-solid fa-box-open"></i> Productos</a>
            <a href="/admin/ver-catalogo" class="nav-btn" target="_blank" style="background: rgba(16, 185, 129, 0.15); color: #6EE7B7;"><i class="fa-solid fa-globe"></i> Ver mi Catálogo</a>
            EXTRA_MENU_PLACEHOLDER
            <a href="/logout" class="nav-btn logout-link"><i class="fa-solid fa-right-from-bracket"></i> Cerrar Sesión</a>
        </div>
        <div class="main-content">
            CONTENT_PLACEHOLDER
        </div>
    </body>
    </html>
    """
    return plantilla_base.replace("EXTRA_MENU_PLACEHOLDER", extra_menu) \
                        .replace("PEDIDOS_BADGE", badge_html)

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
        pedido_id_creado = request.args.get("pedido_id")
        
        pedido_reciente = None
        if pedido_id_creado:
            res_p_rec = supabase.table("pedidos").select("*").eq("id", pedido_id_creado).execute()
            if res_p_rec.data:
                pedido_reciente = res_p_rec.data[0]

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
            
            sch = p.get('stock_ch') or 0
            sm = p.get('stock_m') or 0
            sg = p.get('stock_g') or 0
            sxg = p.get('stock_xg') or 0
            stock_total = sch + sm + sg + sxg
            
            if stock_total <= 0:
                badge_stock = '<span class="badge-stock stock-out">Agotado</span>'
                overlay_agotado = '<div class="sold-out-overlay">AGOTADO</div>'
                btn_html = f'<button class="btn-encargar btn-disabled" disabled><i class="fa-solid fa-ban"></i> Agotado</button>'
                img_class = "img-grayscale"
            else:
                badge_stock = f'<span class="badge-stock stock-in">Stock Total: {stock_total}</span>'
                overlay_agotado = ''
                btn_html = f'''<button class="btn-encargar" onclick="abrirModal('{p.get('id')}', '{p.get('nombre')}', '{p.get('precio')}', {sch}, {sm}, {sg}, {sxg})">
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
                    <div style="font-size: 0.75rem; color: #71717A; margin-bottom: 10px;">
                        CH: {sch} | M: {sm} | G: {sg} | XG: {sxg}
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

    prods_sin_cat = [p for p in productos if not p.get('categoria_id')]
    if prods_sin_cat:
        cards_sin_cat = ""
        for p in prods_sin_cat:
            img_url = p.get('imagen_url') or p.get('imagen') or "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=500"
            sch = p.get('stock_ch') or 0
            sm = p.get('stock_m') or 0
            sg = p.get('stock_g') or 0
            sxg = p.get('stock_xg') or 0
            stock_total = sch + sm + sg + sxg
            
            cards_sin_cat += f"""
            <div class="product-card">
                <div class="img-wrapper"><img src="{img_url}" alt="{p.get('nombre')}"></div>
                <div class="card-content">
                    <span class="category-badge">General</span>
                    <h3 class="product-title">{p.get('nombre')}</h3>
                    <div class="price" style="margin-bottom:12px;">${p.get('precio')} MXN</div>
                    <div style="font-size: 0.75rem; color: #71717A; margin-bottom: 10px;">
                        CH: {sch} | M: {sm} | G: {sg} | XG: {sxg}
                    </div>
                    <button class="btn-encargar" onclick="abrirModal('{p.get('id')}', '{p.get('nombre')}', '{p.get('precio')}', {sch}, {sm}, {sg}, {sxg})">
                        <i class="fa-solid fa-bag-shopping"></i> Encargar Prenda
                    </button>
                </div>
            </div>
            """
        secciones_html += f"""
        <div class="category-section">
            <h2 class="category-section-title">Prendas Disponibles</h2>
            <div class="products-grid">{cards_sin_cat}</div>
        </div>
        """

    plantilla_catalogo = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TIENDA_NOMBRE - Catálogo Exclusivo</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root { --primary: #1E3A8A; --primary-hover: #1D4ED8; --bg: #FAFAFA; --surface: #FFFFFF; --text: #18181B; --muted: #71717A; --border: #E4E4E7; }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
            body { background: var(--bg); color: var(--text); }
            nav { background: var(--surface); border-bottom: 1px solid var(--border); padding: 1.2rem 2.5rem; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 10; }
            .logo { font-size: 1.2rem; font-weight: 800; color: var(--text); text-decoration: none; display: flex; align-items: center; gap: 8px; letter-spacing: -0.5px; }
            .hero { background: #18181B; color: white; padding: 3rem 1.5rem; text-align: center; margin: 0 auto; }
            .hero h1 { font-size: 2rem; font-weight: 800; margin-bottom: 8px; letter-spacing: -0.5px; }
            .hero p { color: #A1A1AA; font-size: 0.95rem; }
            .container-main { max-width: 1200px; margin: 2.5rem auto; padding: 0 1.5rem; }
            .category-section { margin-bottom: 3rem; }
            .category-section-title { font-size: 1.25rem; font-weight: 700; color: var(--text); margin-bottom: 1.2rem; border-bottom: 1px solid var(--border); padding-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
            .products-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1.5rem; }
            .product-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; position: relative; transition: transform 0.2s; }
            .product-card:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.04); }
            .img-wrapper { position: relative; width: 100%; height: 280px; background: #F4F4F5; overflow: hidden; }
            .img-wrapper img { width: 100%; height: 100%; object-fit: cover; }
            .card-content { padding: 1.2rem; display: flex; flex-direction: column; flex: 1; }
            .category-badge { font-size: 0.7rem; color: var(--muted); font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
            .badge-stock { font-size: 0.75rem; font-weight: 600; color: #047857; background: #ECFDF5; padding: 2px 8px; border-radius: 4px; }
            .stock-out { background: #FEF2F2; color: #B91C1C; }
            .product-title { font-size: 1.05rem; margin: 6px 0 4px; font-weight: 700; color: var(--text); }
            .price { font-size: 1.15rem; font-weight: 800; color: var(--text); }
            .btn-encargar { display: flex; align-items: center; justify-content: center; gap: 8px; background: var(--primary); color: white; border: none; padding: 12px; border-radius: 6px; font-weight: 600; cursor: pointer; width: 100%; transition: background 0.2s; }
            .btn-encargar:hover { background: var(--primary-hover); }
            .btn-disabled { background: #E4E4E7; color: #A1A1AA; cursor: not-allowed; }
            .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); backdrop-filter: blur(2px); display: none; align-items: center; justify-content: center; z-index: 100; }
            .modal-box { background: white; padding: 30px; border-radius: 12px; max-width: 450px; width: 90%; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); }
            .alert-toast { background: #065F46; color: white; padding: 16px; border-radius: 8px; max-width: 1200px; margin: 1.5rem auto 0; text-align: center; font-weight: 600; display: flex; justify-content: space-between; align-items: center; }
        </style>
    </head>
    <body>
        <nav>
            <a href="/tienda/TIENDA_SLUG" class="logo"><i class="fa-solid fa-gem"></i> TIENDA_NOMBRE</a>
            <div style="display: flex; gap: 16px; align-items: center;">
                <a href="javascript:void(0);" onclick="consultarMiPedido()" style="color: var(--primary); text-decoration: none; font-weight: 700; font-size: 0.9rem; background: #EFF6FF; padding: 6px 12px; border-radius: 6px;"><i class="fa-solid fa-receipt"></i> Consultar / Cancelar mi Pedido</a>
                <a href="/login" style="color: var(--muted); text-decoration: none; font-weight: 600; font-size: 0.9rem;"><i class="fa-solid fa-lock"></i> Acceso Admin</a>
            </div>
        </nav>

        <section class="hero">
            <h1>Colección Exclusiva</h1>
            <p>Selección de prendas seleccionadas para TIENDA_NOMBRE.</p>
        </section>

        ALERT_TOAST_PLACEHOLDER

        <div class="container-main">
            SECCIONES_HTML_PLACEHOLDER
        </div>

        <div class="modal-overlay" id="modalEncargo">
            <div class="modal-box">
                <h3 style="font-size: 1.25rem; font-weight: 800; margin-bottom: 4px; color: var(--text);">Solicitar Encargo</h3>
                <p id="modalPrendaNombre" style="color: var(--primary); font-weight: 700; margin-bottom: 20px; font-size: 0.95rem;"></p>
                <form action="/hacer-encargo" method="POST">
                    <input type="hidden" name="tienda_id" value="TIENDA_ID">
                    <input type="hidden" name="slug" value="TIENDA_SLUG">
                    <input type="hidden" name="producto_id" id="modalProductoId">
                    
                    <label style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: var(--muted);">Nombre Completo</label>
                    <input type="text" name="nombre_cliente" style="width:100%; padding:10px 12px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px; font-size:0.95rem;" required>
                    
                    <label style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: var(--muted);">Teléfono / WhatsApp</label>
                    <input type="tel" name="telefono" style="width:100%; padding:10px 12px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px; font-size:0.95rem;" required>
                    
                    <label style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: var(--muted);">Selecciona tu Talla</label>
                    <select name="talla" id="selectTalla" style="width:100%; padding:10px 12px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px; font-size:0.95rem; background:white;" required>
                        <option value="" disabled selected>Elige una talla...</option>
                        <option value="CH" id="optCH">Chico (CH)</option>
                        <option value="M" id="optM">Mediano (M)</option>
                        <option value="G" id="optG">Grande (G)</option>
                        <option value="XG" id="optXG">Extra Grande (XG)</option>
                    </select>

                    <label style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: var(--muted);">Método de Pago</label>
                    <select name="metodo_pago" style="width:100%; padding:10px 12px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px; font-size:0.95rem; background:white;" required>
                        <option value="Efectivo al Entregar">Efectivo al Entregar</option>
                        <option value="Transferencia SPEI">Transferencia SPEI</option>
                        <option value="Tarjeta de Débito/Crédito">Tarjeta de Débito / Crédito</option>
                    </select>

                    <label style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: var(--muted);">Tiempo de Entrega Deseado</label>
                    <select name="tiempo_entrega" style="width:100%; padding:10px 12px; margin:6px 0 16px; border:1px solid var(--border); border-radius:6px; font-size:0.95rem; background:white;" required>
                        <option value="Entrega Inmediata (Hoy / Mañana)">⚡ Entrega Inmediata (Hoy / Mañana)</option>
                        <option value="En 2 a 3 días">📦 En 2 a 3 días</option>
                        <option value="Programado (Más de 3 días)">📅 Programado (Más de 3 días)</option>
                    </select>

                    <label style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: var(--muted);">Notas Adicionales</label>
                    <textarea name="notas" rows="2" style="width:100%; padding:10px 12px; margin:6px 0 20px; border:1px solid var(--border); border-radius:6px; font-size:0.95rem; resize:none;"></textarea>
                    
                    <div style="display: flex; gap: 10px;">
                        <button type="submit" style="flex: 1; background: var(--primary); color: white; border: none; padding: 12px; border-radius: 6px; font-weight: 700; cursor: pointer;">Confirmar</button>
                        <button type="button" onclick="cerrarModal()" style="background: #F4F4F5; color: var(--text); border: none; padding: 12px 16px; border-radius: 6px; font-weight: 700; cursor: pointer;">Cancelar</button>
                    </div>
                </form>
            </div>
        </div>

        <script>
            function abrirModal(id, nombre, precio, sch, sm, sg, sxg) {
                document.getElementById('modalProductoId').value = id;
                document.getElementById('modalPrendaNombre').innerText = nombre + " — $" + precio + " MXN";
                
                document.getElementById('optCH').disabled = sch <= 0;
                document.getElementById('optCH').innerText = "Chico (CH) — " + sch + " disp.";
                
                document.getElementById('optM').disabled = sm <= 0;
                document.getElementById('optM').innerText = "Mediano (M) — " + sm + " disp.";
                
                document.getElementById('optG').disabled = sg <= 0;
                document.getElementById('optG').innerText = "Grande (G) — " + sg + " disp.";
                
                document.getElementById('optXG').disabled = sxg <= 0;
                document.getElementById('optXG').innerText = "Extra Grande (XG) — " + sxg + " disp.";
                
                document.getElementById('selectTalla').value = "";
                document.getElementById('modalEncargo').style.display = 'flex';
            }
            function cerrarModal() {
                document.getElementById('modalEncargo').style.display = 'none';
            }
            function consultarMiPedido() {
                const ultimoId = localStorage.getItem('ultimo_pedido_id_TIENDA_SLUG');
                if (!ultimoId) {
                    alert('No encontramos ningún pedido reciente registrado desde este dispositivo.');
                    return;
                }
                window.location.href = '/tienda/TIENDA_SLUG/mi-pedido/' + ultimoId;
            }
        </script>
    </body>
    </html>
    """

    alerta_html = ""
    if msg_exito and pedido_reciente:
        p_id = pedido_reciente.get('id')
        p_cliente = pedido_reciente.get('cliente')
        p_pago = pedido_reciente.get('metodo_pago')
        p_talla = pedido_reciente.get('talla') or 'N/A'
        p_entrega = pedido_reciente.get('tiempo_entrega')
        
        script_guardar_local = f"""
        <script>
            localStorage.setItem('ultimo_pedido_id_{slug}', '{p_id}');
        </script>
        """
        
        texto_whatsapp = f"Hola! Acabo de hacer un encargo en {tienda.get('nombre')}%0A*Folio:* #{p_id}%0A*Cliente:* {p_cliente}%0A*Talla:* {p_talla}%0A*Pago:* {p_pago}%0A*Entrega:* {p_entrega}"
        link_ws = f"https://wa.me/?text={texto_whatsapp}"

        alerta_html = f"""
        {script_guardar_local}
        <div class="container-main" style="margin-bottom: 0;">
            <div class="alert-toast">
                <div>
                    <i class="fa-solid fa-circle-check"></i> ¡Encargo #{p_id} registrado con éxito! 
                    <div style="font-size: 0.85rem; font-weight: 400; margin-top: 4px; opacity: 0.9;">Talla elegida: {p_talla}. Envía tu comprobante o cancela si lo requieres.</div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <a href="{link_ws}" target="_blank" style="background: #25D366; color: white; padding: 8px 14px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 0.85rem; display:flex; align-items:center; gap:6px;"><i class="fa-brands fa-whatsapp"></i> WhatsApp</a>
                    <a href="/tienda/{slug}/mi-pedido/{p_id}" style="background: white; color: #065F46; padding: 8px 14px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 0.85rem;">Ver / Cancelar</a>
                </div>
            </div>
        </div>
        """

    contenido_grid = secciones_html if secciones_html else '<p style="text-align: center; color: var(--muted); padding: 4rem;">No hay prendas disponibles en este momento.</p>'

    html_final = plantilla_catalogo.replace("TIENDA_NOMBRE", tienda.get('nombre')) \
                                  .replace("TIENDA_SLUG", slug) \
                                  .replace("TIENDA_ID", str(tienda_id)) \
                                  .replace("ALERT_TOAST_PLACEHOLDER", alerta_html) \
                                  .replace("SECCIONES_HTML_PLACEHOLDER", contenido_grid)

    return render_template_string(html_final)

@app.route("/hacer-encargo", methods=["POST"])
def hacer_encargo():
    tienda_id = request.form.get("tienda_id")
    slug = request.form.get("slug")
    producto_id = request.form.get("producto_id")
    nombre_cliente = request.form.get("nombre_cliente")
    telefono = request.form.get("telefono")
    talla = request.form.get("talla")
    metodo_pago = request.form.get("metodo_pago")
    tiempo_entrega = request.form.get("tiempo_entrega")
    notas = request.form.get("notas")
    
    try:
        res_ins = supabase.table("pedidos").insert({
            "tienda_id": tienda_id,
            "cliente": nombre_cliente,
            "telefono": telefono,
            "talla": talla,
            "metodo_pago": metodo_pago,
            "tiempo_entrega": tiempo_entrega,
            "notas": notas,
            "producto_id": producto_id,
            "estado": "Pendiente"
        }).execute()
        
        nuevo_pedido_id = res_ins.data[0].get('id') if res_ins.data else 1
        
        res_prod = supabase.table("productos").select("*").eq("id", producto_id).execute()
        if res_prod.data:
            p = res_prod.data[0]
            if talla == 'CH':
                nuevo_stock = max(0, (p.get('stock_ch') or 0) - 1)
                supabase.table("productos").update({"stock_ch": nuevo_stock}).eq("id", producto_id).execute()
            elif talla == 'M':
                nuevo_stock = max(0, (p.get('stock_m') or 0) - 1)
                supabase.table("productos").update({"stock_m": nuevo_stock}).eq("id", producto_id).execute()
            elif talla == 'G':
                nuevo_stock = max(0, (p.get('stock_g') or 0) - 1)
                supabase.table("productos").update({"stock_g": nuevo_stock}).eq("id", producto_id).execute()
            elif talla == 'XG':
                nuevo_stock = max(0, (p.get('stock_xg') or 0) - 1)
                supabase.table("productos").update({"stock_xg": nuevo_stock}).eq("id", producto_id).execute()

        return redirect(url_for("catalogo_tienda", slug=slug, encargo_exito=1, pedido_id=nuevo_pedido_id))
    except Exception as e:
        return f"Error al procesar el encargo: {e}"

@app.route("/tienda/<slug>/mi-pedido/<int:pedido_id>")
def ver_pedido_cliente(slug, pedido_id):
    try:
        res_t = supabase.table("tiendas").select("*").eq("slug", slug).execute()
        if not res_t.data:
            return redirect(url_for("catalogo_tienda", slug=slug))
        tienda = res_t.data[0]
        
        res_p = supabase.table("pedidos").select("*").eq("id", pedido_id).execute()
        if not res_p.data:
            return f"<div style='padding:40px; font-family:sans-serif;'><h2>Pedido no encontrado.</h2><a href='/tienda/{slug}'>Regresar al catálogo</a></div>"
        
        pedido = res_p.data[0]
    except Exception as e:
        return f"Error: {e}"

    estado = pedido.get('estado')
    estado_badge = ""
    acciones_cliente = ""
    
    if estado == 'Completado':
        estado_badge = '<span style="background:#ECFDF5; color:#047857; padding:6px 14px; border-radius:99px; font-weight:700;">Completado / Entregado</span>'
        acciones_cliente = '<p style="color:#71717A; margin-top:20px;">Este pedido ya fue completado y entregado.</p>'
    elif estado == 'Cancelado':
        estado_badge = '<span style="background:#FEF2F2; color:#991B1B; padding:6px 14px; border-radius:99px; font-weight:700;">Cancelado</span>'
        acciones_cliente = '<p style="color:#991B1B; font-weight:600; margin-top:20px;">Has cancelado este pedido con éxito.</p>'
    else:
        estado_badge = '<span style="background:#FEF3C7; color:#B45309; padding:6px 14px; border-radius:99px; font-weight:700;">Pendiente de Revisión</span>'
        acciones_cliente = f'''
            <div style="margin-top: 24px;">
                <a href="/tienda/{slug}/cancelar-mi-pedido/{pedido_id}" onclick="return confirm('¿Deseas cancelar este pedido? La pieza devuelta regresará al inventario de su talla.');" style="background:#EF4444; color:white; padding:12px 20px; border-radius:6px; text-decoration:none; font-weight:700; display:inline-block;"><i class="fa-solid fa-ban"></i> Cancelar mi Pedido</a>
            </div>
        '''

    html_detalle = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Detalle de mi Pedido - {tienda.get('nombre')}</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }}
            body {{ background: #F4F4F5; color: #18181B; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }}
            .card {{ background: white; padding: 40px; border-radius: 12px; border: 1px solid #E4E4E7; width: 100%; max-width: 500px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
            h2 {{ font-size: 1.5rem; font-weight: 800; margin-bottom: 6px; color: #18181B; }}
            p.sub {{ color: #71717A; font-size: 0.9rem; margin-bottom: 24px; }}
            .row {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #F4F4F5; font-size: 0.95rem; }}
            .label {{ color: #71717A; font-weight: 600; }}
            .val {{ font-weight: 700; color: #18181B; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Detalle de tu Encargo #{pedido.get('id')}</h2>
            <p class="sub">{tienda.get('nombre')}</p>
            
            <div style="margin-bottom: 20px; text-align: center;">
                {estado_badge}
            </div>

            <div class="row"><span class="label">Cliente:</span><span class="val">{pedido.get('cliente')}</span></div>
            <div class="row"><span class="label">Teléfono:</span><span class="val">{pedido.get('telefono')}</span></div>
            <div class="row"><span class="label">Talla Seleccionada:</span><span class="val" style="color:var(--primary);">{pedido.get('talla') or 'N/A'}</span></div>
            <div class="row"><span class="label">Método de Pago:</span><span class="val">{pedido.get('metodo_pago')}</span></div>
            <div class="row"><span class="label">Plazo de Entrega:</span><span class="val">{pedido.get('tiempo_entrega')}</span></div>
            <div class="row"><span class="label">Notas:</span><span class="val">{pedido.get('notas') or 'Sin notas'}</span></div>

            {acciones_cliente}

            <div style="margin-top: 24px; text-align: center;">
                <a href="/tienda/{slug}" style="color: #1E3A8A; text-decoration: none; font-weight: 700; font-size: 0.9rem;"><i class="fa-solid fa-arrow-left"></i> Regresar al Catálogo</a>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_detalle)

@app.route("/tienda/<slug>/cancelar-mi-pedido/<int:pedido_id>")
def cancelar_mi_pedido(slug, pedido_id):
    try:
        res_p = supabase.table("pedidos").select("*").eq("id", pedido_id).execute()
        if res_p.data:
            pedido = res_p.data[0]
            prod_id = pedido.get('producto_id')
            talla = pedido.get('talla')
            
            supabase.table("pedidos").update({"estado": "Cancelado"}).eq("id", pedido_id).execute()
            
            if prod_id and talla:
                res_prod = supabase.table("productos").select("*").eq("id", prod_id).execute()
                if res_prod.data:
                    p = res_prod.data[0]
                    if talla == 'CH':
                        supabase.table("productos").update({"stock_ch": (p.get('stock_ch') or 0) + 1}).eq("id", prod_id).execute()
                    elif talla == 'M':
                        supabase.table("productos").update({"stock_m": (p.get('stock_m') or 0) + 1}).eq("id", prod_id).execute()
                    elif talla == 'G':
                        supabase.table("productos").update({"stock_g": (p.get('stock_g') or 0) + 1}).eq("id", prod_id).execute()
                    elif talla == 'XG':
                        supabase.table("productos").update({"stock_xg": (p.get('stock_xg') or 0) + 1}).eq("id", prod_id).execute()
    except Exception as e:
        pass
        
    return redirect(url_for("ver_pedido_cliente", slug=slug, pedido_id=pedido_id))

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
    except:
        pass

    rows = ""
    for t in tiendas:
        t_id = t.get('id')
        t_nombre = t.get('nombre')
        t_slug = t.get('slug')
        activa = t.get('subscripcion_activa', True)
        status_badge = '<span style="background:#ECFDF5; color:#047857; padding:4px 10px; border-radius:99px; font-weight:600; font-size:0.8rem;">Activa</span>' if activa else '<span style="background:#FEF2F2; color:#B91C1C; padding:4px 10px; border-radius:99px; font-weight:600; font-size:0.8rem;">Suspendida</span>'
        btn_accion = f'<a href="/super-admin/cambiar-estatus/{t_id}" style="background:{"#B91C1C" if activa else "#047857"}; color:white; padding:6px 12px; border-radius:4px; text-decoration:none; font-weight:600; font-size:0.85rem;">{"Suspender" if activa else "Activar"}</a>'
        
        rows += f"<tr><td><strong>#{t_id}</strong></td><td><strong>{t_nombre}</strong></td><td><code>/tienda/{t_slug}</code></td><td>{status_badge}</td><td>{btn_accion}</td></tr>"

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Control Maestro</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }}
            body {{ background: #F4F4F5; color: #18181B; padding: 40px; }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }}
            .table-box {{ background: white; padding: 24px; border-radius: 8px; border: 1px solid #E4E4E7; }}
            table {{ width: 100%; border-collapse: collapse; text-align: left; }}
            th {{ padding: 12px 16px; background: #FAFAFA; color: #71717A; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; border-bottom: 1px solid #E4E4E7; }}
            td {{ padding: 16px; border-bottom: 1px solid #E4E4E7; font-size: 0.9rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Control Maestro de Tiendas</h1>
                <a href="/logout" style="background:#EF4444; color:white; padding:10px 16px; border-radius:6px; text-decoration:none; font-weight:600;">Cerrar Sesión</a>
            </div>
            <div class="table-box">
                <table>
                    <thead><tr><th>ID</th><th>Nombre</th><th>Slug</th><th>Estatus</th><th>Acciones</th></tr></thead>
                    <tbody>{rows if rows else '<tr><td colspan="5" style="text-align:center;">No hay tiendas.</td></tr>'}</tbody>
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
            estado = res.data[0].get("subscripcion_activa", True)
            nuevo = not estado
            supabase.table("tiendas").update({"subscripcion_activa": nuevo}).eq("id", id).execute()
    except:
        pass
    return redirect(url_for("super_admin_panel"))

@app.route("/admin")
@login_required
def admin_index():
    tienda_id = session.get("tienda_id")
    nombre_tienda = "Mi Local"
    fecha_corte_str = None
    try:
        res_t = supabase.table("tiendas").select("nombre, fecha_corte").eq("id", tienda_id).execute()
        if res_t.data:
            nombre_tienda = res_t.data[0].get("nombre")
            fecha_corte_str = res_t.data[0].get("fecha_corte")
    except:
        pass

    alerta_corte = ""
    if fecha_corte_str:
        try:
            ahora = datetime.now(timezone.utc)
            f_corte = datetime.fromisoformat(fecha_corte_str.replace('Z', '+00:00'))
            dias = (f_corte - ahora).days
            if dias <= 14 and dias >= 0:
                alerta_corte = f'<div style="background: #FEF3C7; border: 1px solid #F59E0B; padding: 16px; border-radius: 8px; margin-bottom: 24px;"><b>¡Aviso de Corte!</b> Quedan {dias} día(s) para el vencimiento de tu servicio.</div>'
        except:
            pass

    pendientes_count = 0
    try:
        res_ped = supabase.table("pedidos").select("id").eq("tienda_id", tienda_id).eq("estado", "Pendiente").execute()
        pendientes_count = len(res_ped.data) if res_ped.data else 0
    except:
        pass

    alerta_pendientes = f'<div style="background: #FEF3C7; padding: 16px; border-radius: 8px; margin-bottom: 24px;"><b>Tienes {pendientes_count} encargo(s) pendiente(s).</b> <a href="/pedidos">Ver Encargos</a></div>' if pendientes_count > 0 else ''

    content = f"""
        {alerta_corte}
        {alerta_pendientes}
        <div class="header-title"><h1>Panel de {nombre_tienda}</h1></div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; max-width: 600px;">
            <a href="/pedidos" style="text-decoration:none;"><div style="background:white; padding:24px; border-radius:8px; border:1px solid var(--border);"><h3>Encargos</h3></div></a>
            <a href="/productos" style="text-decoration:none;"><div style="background:white; padding:24px; border-radius:8px; border:1px solid var(--border);"><h3>Productos</h3></div></a>
        </div>
    """
    return render_template_string(obtener_sidebar_admin(es_superadmin=session.get("is_superadmin", False), pedidos_pendientes=pendientes_count).replace("CONTENT_PLACEHOLDER", content))

@app.route("/admin/ver-catalogo")
@login_required
def ver_catalogo_admin():
    tienda_id = session.get("tienda_id")
    try:
        res = supabase.table("tiendas").select("slug").eq("id", tienda_id).execute()
        if res.data:
            return redirect(url_for("catalogo_tienda", slug=res.data[0].get("slug")))
    except:
        pass
    return redirect(url_for("admin_index"))

@app.route("/admin/tienda/nueva", methods=["GET", "POST"])
def nueva_tienda():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    error = None
    if request.method == "POST":
        try:
            f_corte = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
            res_t = supabase.table("tiendas").insert({
                "nombre": request.form.get("nombre"),
                "slug": request.form.get("slug"),
                "subscripcion_activa": True,
                "fecha_corte": f_corte
            }).execute()
            if res_t.data:
                supabase.table("administradores").insert({
                    "username": request.form.get("admin_user"),
                    "password": request.form.get("admin_pass"),
                    "tienda_id": res_t.data[0].get("id")
                }).execute()
                return redirect(url_for("catalogo_tienda", slug=request.form.get("slug")))
        except Exception as e:
            error = str(e)
    
    content = f"""
        <h1>Registrar Tienda</h1>
        {f'<p style="color:red;">{error}</p>' if error else ''}
        <form method="POST">
            <label>Nombre</label><input type="text" name="nombre" required style="width:150px; padding:8px; margin-bottom:12px; display:block;">
            <label>Slug</label><input type="text" name="slug" required style="width:150px; padding:8px; margin-bottom:12px; display:block;">
            <label>Admin User</label><input type="text" name="admin_user" required style="width:150px; padding:8px; margin-bottom:12px; display:block;">
            <label>Admin Pass</label><input type="password" name="admin_pass" required style="width:150px; padding:8px; margin-bottom:12px; display:block;">
            <button type="submit" style="background:var(--primary); color:white; padding:10px; border:none; border-radius:6px;">Crear</button>
        </form>
    """
    return render_template_string(obtener_sidebar_admin(es_superadmin=True).replace("CONTENT_PLACEHOLDER", content))

@app.route("/pedidos")
@login_required
def ver_pedidos():
    tienda_id = session.get("tienda_id")
    pedidos = []
    pendientes_count = 0
    try:
        res = supabase.table("pedidos").select("*").eq("tienda_id", tienda_id).order("id", desc=True).execute()
        pedidos = res.data if res.data else []
        for p in pedidos:
            if p.get('estado') == 'Pendiente': pendientes_count += 1
    except:
        pass

    rows = ""
    for ped in pedidos:
        p_id = ped.get('id')
        p_estado = ped.get('estado') or 'Pendiente'
        talla_ped = ped.get('talla') or 'N/A'
        
        if p_estado == 'Completado':
            badge = '<span style="background:#ECFDF5; color:#047857; padding:4px 10px; border-radius:99px; font-weight:700;">Completado</span>'
            acc = f'<a href="/admin/pedido/cancelar/{p_id}" style="background:#FEE2E2; color:#991B1B; padding:6px; border-radius:4px; text-decoration:none;">Cancelar</a>'
        elif p_estado == 'Cancelado':
            badge = '<span style="background:#FEF2F2; color:#991B1B; padding:4px 10px; border-radius:99px; font-weight:700;">Cancelado</span>'
            acc = f'<a href="/admin/pedido/completar/{p_id}" style="background:#ECFDF5; color:#047857; padding:6px; border-radius:4px; text-decoration:none;">Completar</a>'
        else:
            badge = '<span style="background:#FEF3C7; color:#B45309; padding:4px 10px; border-radius:99px; font-weight:700;">Pendiente</span>'
            acc = f'<a href="/admin/pedido/completar/{p_id}" style="background:#047857; color:white; padding:6px; border-radius:4px; text-decoration:none; margin-right:4px;">Listo</a><a href="/admin/pedido/cancelar/{p_id}" style="background:#EF4444; color:white; padding:6px; border-radius:4px; text-decoration:none;">Cancelar</a>'

        rows += f"<tr><td><strong>#{p_id}</strong></td><td>{ped.get('cliente')}</td><td><b>{talla_ped}</b></td><td>{ped.get('metodo_pago')}</td><td>{ped.get('tiempo_entrega')}</td><td>{badge}</td><td>{acc}</td></tr>"

    content = f"""
        <h1>Encargos Recibidos</h1>
        <div class="table-box">
            <table>
                <thead><tr><th>ID</th><th>Cliente</th><th>Talla</th><th>Pago</th><th>Entrega</th><th>Estatus</th><th>Acciones</th></tr></thead>
                <tbody>{rows if rows else '<tr><td colspan="7" style="text-align:center;">No hay encargos.</td></tr>'}</tbody>
            </table>
        </div>
    """
    return render_template_string(obtener_sidebar_admin(es_superadmin=session.get("is_superadmin", False), pedidos_pendientes=pendientes_count).replace("CONTENT_PLACEHOLDER", content))

@app.route("/admin/pedido/completar/<int:id>")
@login_required
def completar_pedido(id):
    try:
        supabase.table("pedidos").update({"estado": "Completado"}).eq("id", id).eq("tienda_id", session.get("tienda_id")).execute()
    except:
        pass
    return redirect(url_for("ver_pedidos"))

@app.route("/admin/pedido/cancelar/<int:id>")
@login_required
def cancelar_pedido(id):
    try:
        supabase.table("pedidos").update({"estado": "Cancelado"}).eq("id", id).eq("tienda_id", session.get("tienda_id")).execute()
    except:
        pass
    return redirect(url_for("ver_pedidos"))

@app.route("/productos")
@login_required
def ver_productos():
    tienda_id = session.get("tienda_id")
    productos = []
    try:
        res = supabase.table("productos").select("*").eq("tienda_id", tienda_id).execute()
        productos = res.data if res.data else []
    except:
        pass

    rows = ""
    for p in productos:
        img = p.get('imagen_url') or "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=500"
        rows += f"""
        <tr>
            <td>#{p.get('id')}</td>
            <td><img src='{img}' style='width:40px;height:40px;object-fit:cover;border-radius:4px;'></td>
            <td>{p.get('nombre')}</td>
            <td><b>${p.get('precio')}</b></td>
            <td>CH:{p.get('stock_ch',0)} | M:{p.get('stock_m',0)} | G:{p.get('stock_g',0)} | XG:{p.get('stock_xg',0)}</td>
            <td>
                <a href='/admin/producto/editar/{p.get('id')}' style='background:#F4F4F5; color:#18181B; padding:6px 12px; border-radius:4px; text-decoration:none; font-weight:600; font-size:0.85rem; margin-right:4px;'><i class='fa-solid fa-pen'></i> Editar</a>
                <a href='/admin/producto/eliminar/{p.get('id')}' onclick="return confirm('¿Estás seguro de eliminar este producto?');" style='background:#FEF2F2; color:#B91C1C; padding:6px 12px; border-radius:4px; text-decoration:none; font-weight:600; font-size:0.85rem;'><i class='fa-solid fa-trash'></i> Borrar</a>
            </td>
        </tr>
        """

    content = f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
            <h1>Inventario</h1>
            <a href="/admin/producto/nuevo" style="background:var(--primary); color:white; padding:10px 16px; border-radius:6px; text-decoration:none; font-weight:700;">Añadir Prenda</a>
        </div>
        <div class="table-box">
            <table>
                <thead><tr><th>ID</th><th>Foto</th><th>Prenda</th><th>Precio</th><th>Stock por Talla</th><th>Acciones</th></tr></thead>
                <tbody>{rows if rows else '<tr><td colspan="6" style="text-align:center;">No hay productos.</td></tr>'}</tbody>
            </table>
        </div>
    """
    return render_template_string(obtener_sidebar_admin(es_superadmin=session.get("is_superadmin", False)).replace("CONTENT_PLACEHOLDER", content))

@app.route("/admin/producto/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_producto():
    tienda_id = session.get("tienda_id")
    if request.method == "POST":
        try:
            supabase.table("productos").insert({
                "tienda_id": tienda_id,
                "nombre": request.form.get("nombre"),
                "precio": float(request.form.get("precio") or 0),
                "stock_ch": int(request.form.get("stock_ch") or 0),
                "stock_m": int(request.form.get("stock_m") or 0),
                "stock_g": int(request.form.get("stock_g") or 0),
                "stock_xg": int(request.form.get("stock_xg") or 0),
                "imagen_url": request.form.get("imagen_recortada")
            }).execute()
            return redirect(url_for("ver_productos"))
        except Exception as e:
            return f"Error: {e}"

    content = """
        <h1>Nuevo Producto con Tallas</h1>
        <form method="POST" style="background:white; padding:24px; border-radius:8px; max-width:500px; border:1px solid var(--border);">
            <input type="hidden" name="imagen_recortada" id="imagen_recortada" required>
            <label>Nombre</label><input type="text" name="nombre" required style="width:100%; padding:8px; margin:6px 0 16px;">
            <label>Precio (MXN)</label><input type="number" step="0.01" name="precio" required style="width:100%; padding:8px; margin:6px 0 16px;">
            
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:16px;">
                <div><label>Stock CH</label><input type="number" name="stock_ch" value="5" style="width:100%; padding:8px;"></div>
                <div><label>Stock M</label><input type="number" name="stock_m" value="5" style="width:100%; padding:8px;"></div>
                <div><label>Stock G</label><input type="number" name="stock_g" value="5" style="width:100%; padding:8px;"></div>
                <div><label>Stock XG</label><input type="number" name="stock_xg" value="5" style="width:100%; padding:8px;"></div>
            </div>

            <label>Foto (Recortar)</label><input type="file" id="inputFoto" accept="image/*" style="width:100%; margin-bottom:16px;" required>
            
            <div id="editorContainer" style="display:none; background:#18181B; padding:10px; border-radius:8px; text-align:center; margin-bottom:16px;">
                <div style="max-height:250px; overflow:hidden; margin-bottom:8px;"><img id="imagenParaRecortar" style="max-width:100%;"></div>
                <button type="button" onclick="cropper.rotate(90)" style="background:#3F3F46; color:white; border:none; padding:6px 10px; border-radius:4px;">Girar</button>
                <button type="button" onclick="confirmarRecorte()" style="background:#047857; color:white; border:none; padding:6px 10px; border-radius:4px;">Aplicar Recorte</button>
            </div>

            <div id="vistaPreviaBox" style="display:none; text-align:center; margin-bottom:16px;">
                <img id="imgResultadoPrev" style="width:80px; height:80px; object-fit:cover; border-radius:6px;">
            </div>

            <button type="submit" style="background:var(--primary); color:white; padding:10px 20px; border:none; border-radius:6px; font-weight:700;">Guardar Producto</button>
        </form>

        
    return render_template_string(obtener_sidebar_admin(es_superadmin=session.get("is_superadmin", False)).replace("CONTENT_PLACEHOLDER", content))

@app.route("/admin/producto/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_producto(id):
    tienda_id = session.get("tienda_id")
    try:
        res_prod = supabase.table("productos").select("*").eq("id", id).eq("tienda_id", tienda_id).execute()
        if not res_prod.data:
            return redirect(url_for("ver_productos"))
        producto = res_prod.data[0]
    except:
        return redirect(url_for("ver_productos"))

    if request.method == "POST":
        nueva_imagen = request.form.get("imagen_recortada")
        imagen_url = nueva_imagen if nueva_imagen and nueva_imagen != "" else producto.get('imagen_url')
        try:
            supabase.table("productos").update({
                "nombre": request.form.get("nombre"),
                "precio": float(request.form.get("precio") or 0),
                "stock_ch": int(request.form.get("stock_ch") or 0),
                "stock_m": int(request.form.get("stock_m") or 0),
                "stock_g": int(request.form.get("stock_g") or 0),
                "stock_xg": int(request.form.get("stock_xg") or 0),
                "imagen_url": imagen_url
            }).eq("id", id).eq("tienda_id", tienda_id).execute()
            return redirect(url_for("ver_productos"))
        except Exception as e:
            return f"Error al actualizar: {e}"

    foto_actual = producto.get('imagen_url') or "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=500"
    content = f"""
        <h1>Editar Producto</h1>
        <form method="POST" style="background:white; padding:24px; border-radius:8px; max-width:500px; border:1px solid var(--border);">
            <input type="hidden" name="imagen_recortada" id="imagen_recortada">
            <label>Nombre</label><input type="text" name="nombre" value="{producto.get('nombre')}" required style="width:100%; padding:8px; margin:6px 0 16px;">
            <label>Precio (MXN)</label><input type="number" step="0.01" name="precio" value="{producto.get('precio')}" required style="width:100%; padding:8px; margin:6px 0 16px;">
            
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:16px;">
                <div><label>Stock CH</label><input type="number" name="stock_ch" value="{producto.get('stock_ch',0)}" style="width:100%; padding:8px;"></div>
                <div><label>Stock M</label><input type="number" name="stock_m" value="{producto.get('stock_m',0)}" style="width:100%; padding:8px;"></div>
                <div><label>Stock G</label><input type="number" name="stock_g" value="{producto.get('stock_g',0)}" style="width:100%; padding:8px;"></div>
                <div><label>Stock XG</label><input type="number" name="stock_xg" value="{producto.get('stock_xg',0)}" style="width:100%; padding:8px;"></div>
            </div>

            <label>Foto Actual</label><div style="margin-bottom:12px;"><img src="{foto_actual}" style="width:80px;height:80px;object-fit:cover;border-radius:6px;"></div>
            <label>Cambiar Foto (Opcional)</label><input type="file" id="inputFoto" accept="image/*" style="width:100%; margin-bottom:16px;">
            
            <div id="editorContainer" style="display:none; background:#18181B; padding:10px; border-radius:8px; text-align:center; margin-bottom:16px;">
                <div style="max-height:250px; overflow:hidden; margin-bottom:8px;"><img id="imagenParaRecortar" style="max-width:100%;"></div>
                <button type="button" onclick="cropper.rotate(90)" style="background:#3F3F46; color:white; border:none; padding:6px 10px; border-radius:4px;">Girar</button>
                <button type="button" onclick="confirmarRecorte()" style="background:#047857; color:white; border:none; padding:6px 10px; border-radius:4px;">Aplicar Recorte</button>
            </div>

            <div id="vistaPreviaBox" style="display:none; text-align:center; margin-bottom:16px;">
                <img id="imgResultadoPrev" style="width:80px; height:80px; object-fit:cover; border-radius:6px;">
            </div>

            <button type="submit" style="background:var(--primary); color:white; padding:10px 20px; border:none; border-radius:6px; font-weight:700;">Actualizar Producto</button>
        </form>

        <script>
            let cropper = null;
            document.getElementById('inputFoto').addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(ev) {
                        document.getElementById('imagenParaRecortar').src = ev.target.result;
                        document.getElementById('editorContainer').style.display = 'block';
                        if (cropper) cropper.destroy();
                        cropper = new Cropper(document.getElementById('imagenParaRecortar'), { aspectRatio: 1, viewMode: 1 });
                    };
                    reader.readAsDataURL(file);
                }
            });
            function confirmarRecorte() {
                const canvas = cropper.getCroppedCanvas({ width: 600, height: 600 });
                const b64 = canvas.toDataURL('image/jpeg');
                document.getElementById('imagen_recortada').value = b64;
                document.getElementById('imgResultadoPrev').src = b64;
                document.getElementById('editorContainer').style.display = 'none';
                document.getElementById('vistaPreviaBox').style.display = 'block';
            }
        </script>
    """
    return render_template_string(obtener_sidebar_admin(es_superadmin=session.get("is_superadmin", False)).replace("CONTENT_PLACEHOLDER", content))

@app.route("/admin/producto/eliminar/<int:id>")
@login_required
def eliminar_producto(id):
    try:
        supabase.table("productos").delete().eq("id", id).eq("tienda_id", session.get("tienda_id")).execute()
    except:
        pass
    return redirect(url_for("ver_productos"))

if __name__ == '__main__':
    app.run(debug=True)
