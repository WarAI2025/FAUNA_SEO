import os
import re
import pandas as pd
import streamlit as st
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="BioTelemetry Pro - Monitor Etológico",
    page_icon="🦅",
    layout="wide"
)

# Estilos CSS personalizados para un diseño profesional oscuro
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

# URL base de tu carpeta de Google Drive para los enlaces de imágenes
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1vx29GXpcFN4iFDt8zwd1qGk18XXEKThG"
ARCHIVO_CSV = "registro_detecciones.csv"

@st.cache_data(ttl=60)
def cargar_datos():
    if not os.path.exists(ARCHIVO_CSV):
        return pd.DataFrame()
    
    df = pd.read_csv(ARCHIVO_CSV, sep=";")
    # Normalización básica de columnas
    if 'Especie' not in df.columns and 'Especie_Gemini' in df.columns:
        df['Especie'] = df['Especie_Gemini']
    if 'Camara' not in df.columns:
        df['Camara'] = "Desconocida"
    if 'Sexo' not in df.columns:
        df['Sexo'] = "Sin identificar"
    if 'Anilla' not in df.columns:
        df['Anilla'] = "Sin anilla"
    if 'Archivo_Imagen' not in df.columns:
        df['Archivo_Imagen'] = ""
    
    return df

df = cargar_datos()

if df.empty:
    st.warning("⚠️ No se encontró el archivo `registro_detecciones.csv` o está vacío. Sube tu archivo CSV al repositorio de GitHub.")
    st.stop()

# --- HEADER ---
st.title("🦅 BioTelemetry Fauna Pro — Suite Etológica")
st.markdown("Análisis de conducta, microhábitats, posturas y censo de fauna ibérica en tiempo real.")

# --- PANEL LATERAL DE FILTROS ---
st.sidebar.header("🎯 Panel de Filtros Relacionales")

# 1. Filtro de Cámara
camaras = ["Todas"] + sorted(df['Camara'].dropna().unique().tolist())
camara_sel = st.sidebar.selectbox("Cámara / Estación", camaras)

# 2. Filtro de Especie
especies = ["Todas"] + sorted(df['Especie'].dropna().unique().tolist())
especie_sel = st.sidebar.selectbox("Especie Identificada", especies)

# 3. Filtro de Sexo
sexos = ["Todos"] + sorted(df['Sexo'].dropna().unique().tolist())
sexo_sel = st.sidebar.selectbox("Dimorfismo / Sexo", sexos)

# 4. Filtro de Anilla
anillas = ["Todos"] + sorted(df['Anilla'].dropna().unique().tolist())
anilla_sel = st.sidebar.selectbox("Marcaje / Anilla", anillas)

# Filtrado del DataFrame
df_filtrado = df.copy()
if camara_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Camara'] == camara_sel]
if especie_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Especie'] == especie_sel]
if sexo_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Sexo'] == sexo_sel]
if anilla_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Anilla'] == anilla_sel]

# --- KPIS PRINCIPALES ---
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Detecciones Filtradas</div><div class="kpi-value">{len(df_filtrado):,}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Taxones Únicos</div><div class="kpi-value">{df_filtrado["Especie"].nunique()}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Cámaras Activas</div><div class="kpi-value">{df_filtrado["Camara"].nunique()}</div></div>', unsafe_allow_html=True)
with col4:
    anilladas = len(df_filtrado[df_filtrado['Anilla'].str.lower() != 'sin anilla']) if 'Anilla' in df_filtrado else 0
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Ejemplares Anillados</div><div class="kpi-value">{anilladas}</div></div>', unsafe_allow_html=True)
with col5:
    pct = (len(df_filtrado) / len(df)) * 100 if len(df) > 0 else 0
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">% del Histórico</div><div class="kpi-value">{pct:.1f}%</div></div>', unsafe_allow_html=True)

st.markdown("---")

# --- GRÁFICOS ANALÍTICOS ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("📊 Especies Coincidentes")
    if not df_filtrado.empty:
        fig_esp = px.bar(
            df_filtrado['Especie'].value_counts().reset_index().head(10),
            x='count', y='Especie', orientation='h',
            color='count', color_continuous_scale='greens',
            labels={'count': 'Número de Detecciones', 'Especie': 'Especie'}
        )
        fig_esp.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig_esp, use_container_width=True)
    else:
        st.info("No hay datos para mostrar con los filtros actual.")

with c2:
    st.subheader("📷 Actividad por Estación / Cámara")
    if not df_filtrado.empty:
        fig_cam = px.pie(
            df_filtrado, names='Camara', hole=0.4,
            color_discrete_sequence=px.colors.sequential.Tealgrn
        )
        fig_cam.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig_cam, use_container_width=True)
    else:
        st.info("No hay datos para mostrar.")

st.markdown("---")

# --- TABLA DINÁMICA DE ACCESO A GOOGLE DRIVE ---
st.subheader("📁 Enlaces Directos a Imágenes en Google Drive")
st.markdown("Selecciona una detección para abrir directamente la búsqueda de la imagen en tu carpeta compartida de Google Drive.")

if not df_filtrado.empty:
    # Preparar tabla para mostrar
    tabla_mostrar = df_filtrado[['Fecha', 'Hora', 'Camara', 'Especie', 'Detecciones', 'Archivo_Imagen']].copy()
    
    # Generar enlace de búsqueda directa en Google Drive por nombre de archivo
    tabla_mostrar['Enlace Drive'] = tabla_mostrar['Archivo_Imagen'].apply(
        lambda img: f"https://drive.google.com/drive/search?q={img}" if pd.notna(img) and img != "" else DRIVE_FOLDER_URL
    )
    
    st.dataframe(
        tabla_mostrar[['Fecha', 'Hora', 'Camara', 'Especie', 'Detecciones', 'Enlace Drive']],
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("No hay registros que coincidan con los filtros seleccionados.")