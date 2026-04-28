import streamlit as st
import pandas as pd
import requests
import re
import os
import zipfile
import io
import shutil
from pathlib import Path
from datetime import datetime

# ─── CONSTANTES ───────────────────────────────────────────────────────────────

BRANDS_LIST = sorted([
    "BYD", "CHANGAN", "CHEVROLET", "CHIREY", "FORD", "FOTON",
    "GAC", "GEELY", "GWM", "HYUNDAI", "JAC", "JAC INDUSTRIA",
    "JETOUR", "KIA", "MAZDA", "MG", "MITSUBISHI", "NISSAN",
    "OMODA", "PEUGEOT", "RAM", "RENAULT", "SEAT", "SUZUKI",
    "TOYOTA", "VOLKSWAGEN",
])

MONTHS_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

BRAND_ALIASES = {
    "VW": "VOLKSWAGEN",
    "VOLKSWAGEN": "VOLKSWAGEN",
    "GWM MOTORS": "GWM",
    "GWM": "GWM",
    "JAC INDUSTRIA": "JAC INDUSTRIA",
    "JAC": "JAC",
}

OFFER_PATTERNS = [
    r"tasa", r"inter[eé]s", r"\bcat\b", r"anualidad",
    r"desde\s*\$", r"\$\s*[\d,]+", r"[\d,]+\s*%",
    r"\d+\s*meses?", r"mensualidad", r"mensuale?s?",
    r"enganche", r"financiam\w*", r"descuento",
    r"oferta", r"promoci[oó]n", r"\bmsi\b",
    r"sin intereses", r"pago\s+mensual", r"bonificaci\w*",
    r"plan de pago", r"cuota", r"cashback",
    r"ahorra", r"regalo", r"bono",
]

MEDIO_MAP = {
    "revista":    "Revista",
    "periódico":  "Periódico",
    "periodico":  "Periódico",
    "radio":      "Radio",
    "televisión": "Televisión",
    "television": "Televisión",
    "tv":         "Televisión",
    "online":     "Online",
    "display":    "Online",
    "text":       "Online",
    "video":      "Online",
}

MAX_PER_MEDIO = 3

# ─── CSS BLOQUES ──────────────────────────────────────────────────────────────

_CSS_BASE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&family=Poppins:wght@400;500;600;700&display=swap');

h1, h2, h3, h4, h5 { font-family: 'Poppins', sans-serif !important; }
p, label, li, td, th, input, select, textarea,
.stMarkdown p, .stText, .stCaption {
    font-family: 'IBM Plex Sans', sans-serif !important;
}

[data-testid="collapsedControl"] span,
[data-testid="stFileUploaderDropzone"] button span:first-child,
[class*="material"], .material-icons, .material-symbols-rounded {
    font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
}

[data-testid="collapsedControl"] {
    display: flex !important; visibility: visible !important; opacity: 1 !important;
}

[data-testid="stPills"] { gap: 4px !important; }
[data-testid="stPills"] button {
    font-size: 10px !important;
    padding: 2px 8px !important;
    min-height: 0 !important;
    line-height: 1.4 !important;
    border-radius: 3px !important;
}

@keyframes drive_car { from { left: -70px; } to { left: 100%; } }
@keyframes road_move { from { background-position: 0 0; } to { background-position: 56px 0; } }
@keyframes blink_txt { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }

.car-road {
    position: relative; width: 100%; height: 60px;
    border-radius: 5px; border: 1px solid; overflow: hidden; margin: 10px 0 4px 0;
}
.car-road-surface { position: absolute; bottom: 0; left: 0; right: 0; height: 20px; border-top: 1px solid; }
.car-road-dashes-anim {
    position: absolute; bottom: 9px; left: 0; right: 0; height: 2px;
    animation: road_move 0.5s linear infinite;
}
.car-road-dashes-static { position: absolute; bottom: 9px; left: 0; right: 0; height: 2px; }

.car-vector {
    position: absolute; bottom: 10px; width: 45px; height: 25px;
    line-height: 1; display: flex; align-items: center; justify-content: center;
}
.car-vector svg { width: 100%; height: 100%; }
.car-body { fill: #888888; }
.car-windows { fill: #aaaaaa; }

.car-driving { left: -70px; animation: drive_car 3.2s linear infinite; }
.car-parked { right: 24px; }

.car-status {
    font-family: 'IBM Plex Sans', sans-serif; font-size: 0.72em;
    font-weight: 500; letter-spacing: 0.12em; margin-bottom: 6px;
}
.car-status-blink { animation: blink_txt 1.4s ease-in-out infinite; }
</style>
"""

_CSS_LIGHT = """
<style>
.stApp { background: #ffffff !important; }
section[data-testid="stSidebar"] { background: #f7f7f7 !important; border-right: 1px solid #e2e2e2 !important; }
h1 { color: #111111 !important; font-size: 1.4em !important; font-weight: 700; border-bottom: 2px solid #111; padding-bottom: 8px; }

.stButton > button[kind="primary"] { background: #111111 !important; color: #ffffff !important; border-radius: 4px !important; }
[data-testid="stBaseButton-pillsActive"] { background: #722F37 !important; color: #ffffff !important; border-color: #722F37 !important; }

.stDownloadButton > button {
    background-color: #722F37 !important;
    color: white !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
}
.stDownloadButton > button:hover {
    background-color: #5a252c !important;
    color: white !important;
}

.car-road { background: #f2f2f2 !important; border-color: #ddd !important; }
.car-road-surface { background: #e4e4e4 !important; border-top-color: #ccc !important; }
.car-road-dashes-anim, .car-road-dashes-static { background: repeating-linear-gradient(90deg, #99999966 0, #99999966 28px, transparent 28px, transparent 56px) !important; }
.car-status { color: #111 !important; }
</style>
"""

_CSS_DARK = """
<style>
.stApp { background: #06080f !important; }
section[data-testid="stSidebar"] { background: #08090f !important; border-right: 1px solid #151d2b !important; }
h1 { color: #00d4aa !important; font-size: 1.4em !important; font-weight: 700; border-bottom: 1px solid #151d2b; padding-bottom: 8px; }
.stButton > button[kind="primary"] { background: #00d4aa !important; color: #06080f !important; border-radius: 4px !important; }
[data-testid="stBaseButton-pillsActive"] { background: #00d4aa !important; color: #06080f !important; }

.stDownloadButton > button {
    background-color: #722F37 !important;
    color: white !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
}

.car-road { background: #080c18 !important; border-color: #1a2535 !important; }
.car-road-surface { background: #0d1520 !important; border-top-color: #1a2535 !important; }
.car-road-dashes-anim, .car-road-dashes-static { background: repeating-linear-gradient(90deg, #00d4aa55 0, #00d4aa55 28px, transparent 28px, transparent 56px) !important; }
.car-status { color: #00d4aa !important; }
</style>
"""

_CSS_AUTO = """
<style>
@media (prefers-color-scheme: light) { """ + _CSS_LIGHT.replace("<style>","").replace("</style>","") + """ }
@media (prefers-color-scheme: dark) { """ + _CSS_DARK.replace("<style>","").replace("</style>","") + """ }
</style>
"""

# ─── CAR ANIMATION ────────────────────────────────────────────────────────────

_CAR_SVG = """
<svg viewBox="0 0 100 50" xmlns="http://www.w3.org/2000/svg">
  <path class="car-body" d="M95 30 L90 28 C85 20, 75 15, 65 15 L35 15 C25 15, 15 20, 10 28 L5 30 C2 31, 2 34, 5 35 L10 35 L12 42 A 8 8 0 0 0 28 42 L72 42 A 8 8 0 0 0 88 42 L90 35 L95 35 C98 34, 98 31, 95 30 Z"/>
  <path class="car-windows" d="M63 18 L37 18 C30 18, 26 21, 25 25 L75 25 C74 21, 70 18, 63 18 Z M50 18 L50 25 M32 25 L68 25" stroke="#ffffff22" stroke-width="1"/>
</svg>
"""

DRIVING_CAR_HTML = f"""
<div class="car-road">
    <div class="car-road-surface"></div>
    <div class="car-road-dashes-anim"></div>
    <div class="car-vector car-driving">{_CAR_SVG}</div>
</div>
<div class="car-status car-status-blink">DESCARGANDO TESTIGOS...</div>
"""

PARKED_CAR_HTML = f"""
<div class="car-road">
    <div class="car-road-surface"></div>
    <div class="car-road-dashes-static"></div>
    <div class="car-vector car-parked">{_CAR_SVG}</div>
</div>
<div class="car-status">PROCESO COMPLETADO</div>
"""

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def find_base_path() -> str:
    return "/tmp/temp_downloads"

def clean_temp_downloads():
    path = find_base_path()
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)

def detect_source(df: pd.DataFrame) -> str:
    cols = set(df.columns)
    if "Testigo" in cols: return "auditsa"
    if "Advertisement" in cols: return "admetricks"
    return "unknown"

def normalize_brand(raw: str) -> str:
    b = str(raw).strip().upper()
    return BRAND_ALIASES.get(b, b)

def normalize_medio(raw: str) -> str:
    return MEDIO_MAP.get(str(raw).strip().lower(), str(raw).strip().title())

def brand_in_selection(raw: str, selected: list[str]) -> bool:
    return normalize_brand(raw) in [normalize_brand(s) for s in selected]

def has_offer(text) -> bool:
    if not text or (isinstance(text, float) and pd.isna(text)): return False
    t = str(text).lower()
    return any(re.search(p, t) for p in OFFER_PATTERNS)

def get_extension(content_type: str, url: str) -> str:
    ct = content_type.lower()
    for token, ext in [("jpeg", ".jpg"), ("jpg", ".jpg"), ("png", ".png"), ("gif", ".gif"), ("pdf", ".pdf"), ("mp4", ".mp4"), ("webp", ".webp")]:
        if token in ct: return ext
    _, ext = os.path.splitext(url.split("?")[0])
    return ext if ext else ".jpg"

# ── CAMBIO 1: sanitize ahora convierte a minúsculas ──
def sanitize(s: str, max_len: int = 50) -> str:
    return re.sub(r"[^\w\-]", "_", str(s).strip().lower())[:max_len]

# ── CAMBIO 2: get_save_folder usa marca en minúsculas ──
def get_save_folder(base: str, marca: str, month_folder: str) -> Path:
    folder = Path(base) / month_folder / normalize_brand(marca).lower()
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def download_file(url: str, folder: Path, filename_base: str):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        r = requests.get(url, headers=headers, timeout=30, stream=True)
        r.raise_for_status()
        ext = get_extension(r.headers.get("content-type", ""), url)
        fname = f"{filename_base}{ext}"
        fpath = folder / fname
        with open(fpath, "wb") as f:
            for chunk in r.iter_content(65536): f.write(chunk)
        return True, fname, None
    except Exception as e:
        return False, None, str(e)

# ─── PROCESAMIENTO ────────────────────────────────────────────────────────────

def process_file(df, source, selected_brands, base_path, month_folder, prog_bar, status_txt):
    results = []
    if source == "auditsa":
        url_col, desc_col, fuente_col, medio_col = ("Testigo", "Texto de nota", "Fuente", "Medio")
    else:
        url_col, desc_col, fuente_col, medio_col = ("Advertisement", "Nombre de campaña", "Sitio web", "Formato")

    df = df[df["Marca"].apply(lambda x: brand_in_selection(x, selected_brands))].copy()
    df = df.drop_duplicates(subset=[url_col])
    df["_marca_norm"] = df["Marca"].apply(normalize_brand)
    df["_medio_norm"] = df[medio_col].apply(normalize_medio) if medio_col in df.columns else "Online"
    df = df.groupby(["_marca_norm", "_medio_norm"], group_keys=False).apply(lambda g: g.head(MAX_PER_MEDIO)).reset_index(drop=True)

    total = len(df)
    if total == 0: return results

    for i, (_, row) in enumerate(df.iterrows()):
        marca  = normalize_brand(row.get("Marca", ""))
        fuente = sanitize(row.get(fuente_col, "desconocido"))
        medio  = normalize_medio(row.get(medio_col, "")) if medio_col in df.columns else "Online"
        fecha  = row.get("Fecha", datetime.now())
        url    = str(row.get(url_col, "")).strip()
        desc = str(row.get(desc_col, ""))
        if source == "admetricks": desc = f"{desc} {str(row.get('Etiquetas de campaña', ''))}"

        prog_bar.progress((i + 1) / total)
        status_txt.text(f"{i+1}/{total}   {marca}   ({medio})")

        if not url or url in ("nan", ""):
            results.append({"Marca": marca, "Medio": medio, "Fuente": fuente, "Fecha": str(fecha)[:10], "Exito": False, "Archivo": "", "Error": "URL vacia", "Oferta Comercial": has_offer(desc), "Texto": desc[:300]})
            continue

        fecha_str  = fecha.strftime("%Y-%m-%d") if hasattr(fecha, "strftime") else str(fecha)[:10]
        folder     = get_save_folder(base_path, marca, month_folder)
        fname_base = sanitize(f"{marca}_{fuente}_{fecha_str}")
        ok, fname, err = download_file(url, folder, fname_base)
        results.append({"Marca": marca, "Medio": medio, "Fuente": fuente, "Fecha": fecha_str, "Exito": ok, "Archivo": fname or "", "Error": err or "", "Oferta Comercial": has_offer(desc), "Texto": desc[:300] if has_offer(desc) else ""})
    return results

def build_zip(base_path: str, month_folder: str) -> bytes | None:
    target = Path(base_path) / month_folder
    if not target.exists(): return None
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(target.rglob("*")):
            if file.is_file(): zf.write(file, Path(month_folder) / file.relative_to(target))
    buf.seek(0)
    return buf.read()

# ─── UI ───────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Testigos Competencia", layout="wide")

if "theme_mode" not in st.session_state: st.session_state.theme_mode = "◑"
if "brand_pills_widget" not in st.session_state: st.session_state["brand_pills_widget"] = BRANDS_LIST
if "processed" not in st.session_state: st.session_state.processed = False

theme_icon = st.session_state.theme_mode
if theme_icon == "☀️": st.markdown(_CSS_BASE + _CSS_LIGHT, unsafe_allow_html=True)
elif theme_icon == "🌙": st.markdown(_CSS_BASE + _CSS_DARK, unsafe_allow_html=True)
else: st.markdown(_CSS_BASE + _CSS_AUTO, unsafe_allow_html=True)

st.title("Testigos — Competencia Automotriz")

with st.sidebar:
    tema = st.segmented_control("Tema", options=["☀️", "◑", "🌙"], default=st.session_state.theme_mode, key="tema_seg")
    if tema and tema != st.session_state.theme_mode:
        st.session_state.theme_mode = tema
        st.rerun()

    st.divider()
    st.header("Configuracion")
    st.info("La app guardará los archivos temporalmente en el servidor. Al terminar, usa el botón rojo vino para descargar el ZIP.")

    st.divider()
    st.subheader("Marcas competencia")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Todas", use_container_width=True):
            st.session_state["brand_pills_widget"] = BRANDS_LIST
            st.rerun()
    with c2:
        if st.button("Ninguna", use_container_width=True):
            st.session_state["brand_pills_widget"] = []
            st.rerun()

    selected_brands = st.pills("Marcas", BRANDS_LIST, selection_mode="multi", key="brand_pills_widget", label_visibility="collapsed") or []

st.subheader("Archivos a procesar")
uploaded_files = st.file_uploader("Sube archivos Excel (.xlsx):", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    default_folder = f"{MONTHS_ES[datetime.now().month]} {datetime.now().year}"
    month_folder = st.text_input("Nombre de la carpeta del mes:", value=default_folder)

    if st.button("Procesar archivos", type="primary", use_container_width=True):
        if not selected_brands: st.error("Selecciona marcas.")
        elif not month_folder.strip(): st.error("Escribe el nombre del mes.")
        else:
            # ── CAMBIO 3: normalizar month_folder a minúsculas con guiones bajos ──
            month_folder = month_folder.strip().lower().replace(" ", "_")
            clean_temp_downloads()
            all_results = []
            base_path = find_base_path()
            car_slot = st.empty()
            car_slot.markdown(DRIVING_CAR_HTML, unsafe_allow_html=True)

            for uf in uploaded_files:
                try:
                    df = pd.read_excel(uf)
                    source = detect_source(df)
                    if source == "unknown": continue
                    prog = st.progress(0); status = st.empty()
                    results = process_file(df, source, selected_brands, base_path, month_folder, prog, status)
                    all_results.extend(results)
                except Exception as e: st.error(f"Error en {uf.name}: {e}")

            car_slot.markdown(PARKED_CAR_HTML, unsafe_allow_html=True)
            if all_results:
                st.session_state.processed = True
                st.session_state.df_res = pd.DataFrame(all_results)
                st.session_state.month_folder = month_folder

if st.session_state.processed:
    st.divider()
    df_res = st.session_state.df_res
    month_folder = st.session_state.month_folder

    zip_data = build_zip(find_base_path(), month_folder)
    if zip_data:
        st.download_button(
            label="📁 DESCARGAR TODOS LOS TESTIGOS (ZIP)",
            data=zip_data,
            file_name=f"{month_folder}.zip",
            mime="application/zip",
            use_container_width=True,
        )

    st.divider()
    st.success("¡Proceso terminado!")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(df_res))
    c2.metric("OK", int(df_res["Exito"].sum()))
    c3.metric("Ofertas", int(df_res["Oferta Comercial"].sum()))

    t1, t2, t3 = st.tabs(["Descargados", "Ofertas", "Errores"])
    with t1: st.dataframe(df_res[df_res["Exito"]][["Marca", "Medio", "Fuente", "Fecha", "Archivo"]], use_container_width=True)
    with t2: st.dataframe(df_res[df_res["Oferta Comercial"]][["Marca", "Medio", "Fuente", "Fecha", "Texto"]], use_container_width=True)
    with t3: st.dataframe(df_res[~df_res["Exito"]][["Marca", "Medio", "Fuente", "Fecha", "Error"]], use_container_width=True)
