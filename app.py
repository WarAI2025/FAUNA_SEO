import os
import re
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="BioTelemetry Pro - Monitor Etológico",
    page_icon="🦅",
    layout="wide"
)

st.markdown("""
    <style>
    .main { background-color: #070b12; color: #f8fafc; }
    .kpi-card {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        padding: 16px;
        border-radius: 12px;
        text-align: center;
    }
    .kpi-value { font-size: 1.8rem; font-weight: 800; color: #10b981; }
    .kpi-label { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1vx29GXpcFN4iFDt8zwd1qGk18XXEKThG"
ARCHIVO_CSV = "registro_detecciones.csv"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/WarAI2025/FAUNA_SEO/main/animales_detectados/"

@st.cache_data(ttl=60)
def cargar_datos():
    if not os.path.exists(ARCHIVO_CSV):
        return pd.DataFrame()
    df = pd.read_csv(ARCHIVO_CSV, sep=";")
    if 'Especie' not in df.columns and 'Especie_Gemini' in df.columns:
        df['Especie'] = df['Especie_Gemini']
    if 'Camara' not in df.columns:
        df['Camara'] = "Desconocida"
    if 'Fecha' not in df.columns:
        df['Fecha'] = ""
    if 'Archivo_Imagen' not in df.columns:
        df['Archivo_Imagen'] = ""
    
    try:
        df['Temp_Datetime'] = pd.to_datetime(df['Fecha'] + ' ' + df['Hora'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        df = df.sort_values(by='Temp_Datetime', ascending=False).drop(columns=['Temp_Datetime'])
    except Exception:
        df = df.iloc[::-1]
        
    return df

df = cargar_datos()

if df.empty:
    st.warning("⚠️ No se encontró el archivo `registro_detecciones.csv` o está vacío.")
    st.stop()

st.title("🦅 BioTelemetry Fauna Pro — Suite Etológica")
st.markdown("Análisis de conducta, microhábitats, posturas y censo de fauna ibérica en tiempo real.")

# --- PANEL LATERAL DE FILTROS ---
st.sidebar.header("🎯 Panel de Filtros Relacionales")

camaras = ["Todas"] + sorted(df['Camara'].dropna().unique().tolist())
camara_sel = st.sidebar.selectbox("Cámara / Estación", camaras)

especies = ["Todas"] + sorted(df['Especie'].dropna().unique().tolist())
especie_sel = st.sidebar.selectbox("Especie Identificada", especies)

fechas = ["Todas"] + df['Fecha'].dropna().unique().tolist()
fecha_sel = st.sidebar.selectbox("Fecha de Detección", fechas)

df_filtrado = df.copy()
if camara_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Camara'] == camara_sel]
if especie_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Especie'] == especie_sel]
if fecha_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Fecha'] == fecha_sel]

# --- KPIS PRINCIPALES ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Detecciones Filtradas</div><div class="kpi-value">{len(df_filtrado):,}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Taxones Únicos</div><div class="kpi-value">{df_filtrado["Especie"].nunique()}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Cámaras Activas</div><div class="kpi-value">{df_filtrado["Camara"].nunique()}</div></div>', unsafe_allow_html=True)
with col4:
    pct = (len(df_filtrado) / len(df)) * 100 if len(df) > 0 else 0
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">% del Histórico</div><div class="kpi-value">{pct:.1f}%</div></div>', unsafe_allow_html=True)

st.markdown("---")

# --- GALERÍA VISUAL DE IMÁGENES SEGÚN SELECCIÓN ---
st.subheader("📸 Galería de Fotogramas Coincidentes (Visualización Directa)")
st.markdown("Las imágenes se muestran automáticamente a continuación según los filtros seleccionados (ordenadas de la más actual a la más antigua).")

if not df_filtrado.empty:
    num_mostrar = min(len(df_filtrado), 30)
    st.info(f"Mostrando los primeros {num_mostrar} fotogramas de un total de {len(df_filtrado)} registros coincidentes.")
    
    cols = st.columns(3)
    for idx, (row_idx, row) in enumerate(df_filtrado.head(num_mostrar).iterrows()):
        img_name = row.get('Archivo_Imagen', '')
        camara = row.get('Camara', '')
        fecha = row.get('Fecha', '')
        hora = row.get('Hora', '')
        especie = row.get('Especie', '')
        
        img_url = GITHUB_RAW_BASE + img_name if img_name else ""
        drive_search = f"https://drive.google.com/drive/search?q={img_name}" if img_name else DRIVE_FOLDER_URL
        
        with cols[idx % 3]:
            st.markdown(f"**{especie}**")
            st.caption(f"📍 {camara} | 📅 {fecha} {hora}")
            if img_url:
                try:
                    st.image(img_url, use_container_width=True)
                except Exception:
                    st.warning("No se pudo cargar la miniatura.")
            st.markdown(f"[🔗 Buscar en Google Drive]({drive_search})")
            st.markdown("---")
else:
    st.warning("No hay registros que coincidan con los filtros seleccionados.")
