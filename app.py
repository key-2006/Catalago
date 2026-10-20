from flask import Flask, request, render_template_string, redirect, url_for, session
import os
import base64
from functools import wraps
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "clave_secreta_para_sesiones_tienda_123"

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

# Credenciales de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bkxniuudzmxcpouzgqxm.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_WUzLfoiBMtr7zZknBUo-_w_8W4MwY8S")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    supabase = None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
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
        body { background-color: #0F172A; color: white; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
        .card-suspendido { background: #1E293B; border: 1px solid #334155; padding: 40px 30px; border-radius: 20px; text-align: center; max-width: 480px; width: 100%; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .icon-box { background: rgba(239, 68, 68, 0.15); color: #EF4444; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; font-size: 2.2rem; border: 2px solid rgba(239, 68, 68, 0.3); }
        h1 { font-size: 1.6rem; font-weight: 800; margin-bottom: 12px; color: #F8FAFC; }
        p { color: #94A3B8; font-size: 0.95rem; line-height: 1.5; margin-bottom: 24px; }
        .badge-status { background: #334155; color: #CBD5E1; padding: 8px 16px; border-radius: 99px; font-weight: 600; font-size: 0.85rem; display: inline-block; }
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
        :root { --sidebar-bg: #0F172A; --sidebar-hover: #1E293B; --primary: #4F46E5; --primary-hover: #4338CA; --bg: #F8FAFC; --surface: #FFFFFF; --text-main: #1E293B; --text-muted: #64748B; --border: #E2E8F0; --danger: #EF4444; --radius: 12px; }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        body { display: flex; min-height: 100vh; background-color: var(--bg); color: var(--text-main); }
        .sidebar { width: 260px; background-color: var(--sidebar-bg); padding: 24px 16px; color: #F8FAFC; display: flex; flex-direction: column; gap: 6px; }
        .brand { display: flex; align-items: center; gap: 12px; padding: 0 12px 20px 12px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 12px; }
        .brand i { font-size: 1.5rem; color: #818CF8; }
        .brand h2 { font-size: 1.1rem; font-weight: 700; }
        .brand p { font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; }
        .nav-btn { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 8px; color: #94A3B8; text-decoration: none; font-weight: 600; font-size: 0.9rem; transition: all 0.2s; }
        .nav-btn:hover, .nav-btn.active { background-color: var(--sidebar-hover); color: #FFFFFF; }
        .nav-btn i { font-size: 1.1rem; width: 20px; text-align: center; }
        .nav-btn.logout-link { margin-top: auto; background: rgba(239, 68, 68, 0.15); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.2); }
        .nav-btn.logout-link:hover { background: var(--danger); color: white; }
        .main-content { flex: 1; padding: 32px; overflow-y: auto; }
        .header-title { margin-bottom: 24px; }
        .header-title h1 { font-size: 1.75rem; font-weight: 800; color: #0F172A; }
        .table-box { background: var(--surface); padding: 24px; border-radius: var(--radius); border: 1px solid var(--border); box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        table { width: 100%; border-collapse: collapse; text-align: left; }
        th { padding: 12px 16px; background: #F8FAFC; color: var(--text-muted); font-size: 0.8rem; font-weight: 700; text-transform: uppercase; border-bottom: 1px solid var(--border); }
        td { padding: 16px; border-bottom: 1px solid var(--border); font-size: 0.9rem; vertical-align: middle; }
        .img-preview-thumb { width: 50px; height: 50px; object-fit: cover; border-radius: 8px; border: 1px solid var(--border); }
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
        <a href="/" class="nav-btn" target="_blank"><i class="fa-solid fa-globe"></i> Ver Catálogo Público</a>
        <a href="/logout" class="nav-btn logout-link"><i class="fa-solid fa-right-from-bracket"></i> Cerrar Sesión</a>
    </div>
    <div class="main-content">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

@app.route("/")
def inicio_raiz():
    return redirect(url_for("catalogo_tienda", slug="vibe-apparel"))

@app.route("/tienda/<slug>")
def catalogo_tienda(slug):
    try:
        res_tienda = supabase.table("tiendas").select("*").eq("slug", slug).execute()
        
        if not res_tienda.data:
            supabase.table("tiendas").insert({
                "nombre": "Vibe Apparel",
                "slug": slug,
                "subscripcion_activa": True
            }).execute()
            res_tienda = supabase.table("tiendas").select("*").eq("slug", slug).execute()

        tienda = res_tienda.data[0]
        tienda_id = tienda.get("id")
        
        if not tienda.get("subscripcion_activa", True):
            return render_template_string(PLANTILLA_SUSPENDIDO)

        res_cat = supabase.table("categorias").select("*").execute()
        categorias = res_cat.data if res_cat.data else []
        
        cat_id_sel = request.args.get("cat")
        msg_exito = request.args.get("encargo_exito")
        
        res_prod = supabase.table("productos").select("*").execute()
        todos_productos = res_prod.data if res_prod.data else []

        if cat_id_sel:
            productos = [p for p in todos_productos if str(p.get("categoria_id") or p.get("id_categoria") or "") == str(cat_id_sel)]
        else:
            productos = todos_productos

    except Exception as e:
        return f"<div style='padding:40px; font-family:sans-serif;'><h2>Ocurrió un error al cargar la tienda:</h2><p>{e}</p></div>", 500

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
    cat_html = f'<li class="cat-item"><a href="/tienda/{slug}" class="{active_all}">Todas las prendas</a></li>'
    
    for c in categorias:
        cat_id = c.get('id')
        nombre_cat = c.get('nombre') or 'Categoría'
        active_class = 'active-cat' if str(cat_id_sel) == str(cat_id) else ''
        cat_html += f'<li class="cat-item"><a href="/tienda/{slug}?cat={cat_id}" class="{active_class}">{nombre_cat}</a></li>'

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{tienda.get('nombre')} - Catálogo Digital</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root {{ --primary: #4F46E5; --bg: #F8FAFC; --surface: #FFFFFF; --text: #0F172A; --muted: #64748B; }}
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }}
            body {{ background: var(--bg); color: var(--text); }}
            nav {{ background: var(--surface); border-bottom: 1px solid #E2E8F0; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 10; }}
            .logo {{ font-size: 1.3rem; font-weight: 800; color: var(--primary); text-decoration: none; display: flex; align-items: center; gap: 8px; }}
            .hero {{ background: linear-gradient(135deg, #4F46E5, #7C3AED); color: white; padding: 2.5rem 1.5rem; text-align: center; margin: 1.5rem auto; max-width: 1200px; border-radius: 16px; }}
            .payments-bar {{ background: #FFFFFF; border: 1px solid #E2E8F0; max-width: 1200px; margin: 0 auto 1.5rem; padding: 1rem 1.5rem; border-radius: 12px; display: flex; align-items: center; justify-content: space-around; flex-wrap: wrap; gap: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
            .payment-item {{ display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 0.9rem; color: #475569; }}
            .layout {{ max-width: 1200px; margin: 0 auto 2rem; padding: 0 1.5rem; display: grid; grid-template-columns: 240px 1fr; gap: 2rem; }}
            .sidebar-cat {{ background: var(--surface); padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; height: fit-content; }}
            .cat-list {{ list-style: none; margin-top: 1rem; }}
            .cat-item a {{ display: block; padding: 8px 12px; color: var(--muted); text-decoration: none; border-radius: 6px; font-weight: 500; }}
            .cat-item a.active-cat {{ background: #EEF2FF; color: var(--primary); font-weight: 700; }}
            .products-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 1.5rem; }}
            .product-card {{ background: var(--surface); border: 1px solid #E2E8F0; border-radius:
