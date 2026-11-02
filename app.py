
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
    return df

df = cargar_datos()

if df.empty:
    st.warning("⚠️ No se encontró el archivo `registro_detecciones.csv` o está vacío.")
    st.stop()

st.title("🦅 BioTelemetry Fauna Pro — Suite Etológica")
st.markdown("Análisis de conducta, microhábitats, posturas y censo de fauna ibérica en tiempo real.")

# --- PANEL LATERAL DE FILTROS ---
st.sidebar.header("🎯 Panel de Filtros Relacionales")

# 1. Cámara
camaras = ["Todas"] + sorted(df['Camara'].dropna().unique().tolist())
camara_sel = st.sidebar.selectbox("Cámara / Estación", camaras)

# 2. Especie
especies = ["Todas"] + sorted(df['Especie'].dropna().unique().tolist())
especie_sel = st.sidebar.selectbox("Especie Identificada", especies)

# 3. Fecha (Sustituyendo Dimorfismo y Marcaje)
fechas = ["Todas"] + sorted(df['Fecha'].dropna().unique().tolist())
fecha_sel = st.sidebar.selectbox("Fecha de Detección", fechas)

# Filtrado
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

# --- VISUALIZADOR Y ENLACES DIRECTOS A IMÁGENES ---
st.subheader("📁 Visualizador y Enlaces Directos a Imágenes en Google Drive")
st.markdown("Selecciona una línea de la tabla inferior para ver la información detallada y abrir o comprobar la imagen en Google Drive al instante.")

if not df_filtrado.empty:
    # Añadir columna de enlace a Google Drive
    df_display = df_filtrado.copy()
    df_display['Enlace Drive'] = df_display['Archivo_Imagen'].apply(
        lambda img: f"https://drive.google.com/drive/search?q={img}" if pd.notna(img) and img != "" else DRIVE_FOLDER_URL
    )

    # Selector de registro para inspeccionar imagen y detalles
    opciones_indices = df_display.index.tolist()
    
    # Tabla interactiva
    st.dataframe(
        df_display[['Fecha', 'Hora', 'Camara', 'Especie', 'Detecciones', 'Enlace Drive']],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### 🔍 Inspección Rápida del Fotograma Seleccionado")
    idx_seleccionado = st.selectbox("Elige un registro de la lista (por su número de índice):", opciones_indices)
    
    if idx_seleccionado is not None:
        row_sel = df_display.loc[idx_seleccionado]
        col_i1, col_i2 = st.columns([1, 2])
        with col_i1:
            st.markdown(f"**Cámara:** {row_sel['Camara']}")
            st.markdown(f"**Fecha y Hora:** {row_sel['Fecha']} - {row_sel['Hora']}")
            st.markdown(f"**Especie:** {row_sel['Especie']}")
            st.markdown(f"**Descripción:** {row_sel.get('Descripcion_Detallada', 'Sin descripción')}")
            img_name = row_sel['Archivo_Imagen']
            link_Drive = f"https://drive.google.com/drive/search?q={img_name}" if img_name else DRIVE_FOLDER_URL
            st.markdown(f"🔗 [Abrir imagen exacta en Google Drive]({link_Drive})", unsafe_allow_html=True)
        with col_i2:
            st.info(f"📸 Archivo de imagen asociado: `{img_name}`. Haz clic en el enlace de la izquierda para buscar y comprobar el fotograma directamente en tu carpeta compartida de Google Drive.")
else:
    st.warning("No hay registros que coincidan con los filtros seleccionados.")
