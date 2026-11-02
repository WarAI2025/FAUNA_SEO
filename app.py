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
    
    try:
        df['Temp_Datetime'] = pd.to_datetime(df['Fecha'] + ' ' + df['Hora'], errors='coerce')
        mask_nat = df['Temp_Datetime'].isna()
        if mask_nat.any():
            df.loc[mask_nat, 'Temp_Datetime'] = pd.to_datetime(df.loc[mask_nat, 'Fecha'], format='%Y-%m-%d', errors='coerce')
        df['Fecha'] = df['Temp_Datetime'].dt.strftime('%d/%m/%Y').fillna(df['Fecha'])
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

# --- INSPECTOR RÁPIDO DE FOTOGRAMAS ---
st.subheader("📸 Inspector Directo de Fotogramas (Últimos 10 registros)")
st.markdown("Selecciona cualquier registro de la lista desplegable para ver su información completa y abrir su búsqueda exacta en Google Drive al instante.")

if not df_filtrado.empty:
    df_ultimas_10 = df_filtrado.head(10).reset_index(drop=True)
    
    # Crear opciones descriptivas para el selectbox
    opciones_select = [
        f"[{row['Fecha']} {row['Hora']}] - {row['Especie']} ({row['Camara']}) - Archivo: {row['Archivo_Imagen']}"
        for _, row in df_ultimas_10.iterrows()
    ]
    
    seleccion = st.selectbox("🎯 Elige un avistamiento para inspeccionar:", opciones_select)
    
    if seleccion:
        # Encontrar el índice seleccionado
        idx_sel = opciones_select.index(seleccion)
        row_sel = df_ultimas_10.iloc[idx_sel]
        
        img_name = row_sel.get('Archivo_Imagen', '')
        drive_search = f"https://drive.google.com/drive/search?q={img_name}" if img_name else DRIVE_FOLDER_URL
        
        c_det1, c_det2 = st.columns([1, 1])
        with c_det1:
            st.markdown(f"### 📋 Detalles del Evento")
            st.markdown(f"**Especie:** {row_sel.get('Especie', 'N/D')}")
            st.markdown(f"**Cámara / Estación:** {row_sel.get('Camara', 'N/D')}")
            st.markdown(f"**Fecha y Hora:** {row_sel.get('Fecha', '')} a las {row_sel.get('Hora', '')}")
            st.markdown(f"**Detección Primaria (YOLO):** {row_sel.get('Detecciones', 'N/D')}")
            st.markdown(f"**Archivo de Imagen:** `{img_name}`")
            st.markdown(f"🔗 **[Abrir carpeta o buscar imagen en Google Drive]({drive_search})**")
            
        with c_det2:
            st.markdown(f"### 🔍 Vista del Registro")
            st.info(f"Para ver la fotografía en alta resolución con su cuadro delimitador (BBox), haz clic en el enlace de la izquierda para abrir el archivo exacto (`{img_name}`) directamente en tu Google Drive.")
            
    st.markdown("---")
    st.subheader("📋 Tabla Resumen de Registros Coincidentes")
    st.dataframe(
        df_filtrado[['Fecha', 'Hora', 'Camara', 'Especie', 'Detecciones', 'Archivo_Imagen']],
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("No hay registros que coincidan con los filtros seleccionados.")
