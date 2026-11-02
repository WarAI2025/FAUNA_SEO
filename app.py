import os
import pandas as pd
import streamlit as st

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

ARCHIVO_CSV = "registro_detecciones.csv"
# URL base oficial de tu repositorio en GitHub para renderizar las imágenes instantáneamente
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/WarAI2025/FAUNA_SEO/main/"

@st.cache_data(ttl=10)
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
st.markdown("Sincronización en tiempo real de registros, cámaras y fotogramas.")

# --- FILTROS EN CASCADA ---
st.sidebar.header("🎯 Panel de Filtros Relacionales")

if 'camara_sel' not in st.session_state: st.session_state.camara_sel = "Todas"
if 'especie_sel' not in st.session_state: st.session_state.especie_sel = "Todas"
if 'fecha_sel' not in st.session_state: st.session_state.fecha_sel = "Todas"

def obtener_filtrado_excluyendo(campo_excluido):
    temp_df = df.copy()
    c_sel = st.session_state.get('camara_sel', 'Todas')
    e_sel = st.session_state.get('especie_sel', 'Todas')
    f_sel = st.session_state.get('fecha_sel', 'Todas')
    
    if campo_excluido != 'camara' and c_sel != "Todas":
        temp_df = temp_df[temp_df['Camara'] == c_sel]
    if campo_excluido != 'especie' and e_sel != "Todas":
        temp_df = temp_df[temp_df['Especie'] == e_sel]
    if campo_excluido != 'fecha' and f_sel != "Todas":
        temp_df = temp_df[temp_df['Fecha'] == f_sel]
    return temp_df

df_exc_camara = obtener_filtrado_excluyendo('camara')
camaras_disp = ["Todas"] + sorted(df_exc_camara['Camara'].dropna().unique().tolist())
if st.session_state.camara_sel not in camaras_disp: st.session_state.camara_sel = "Todas"
camara_sel = st.sidebar.selectbox("Cámara / Estación", camaras_disp, key='camara_sel')

df_exc_especie = obtener_filtrado_excluyendo('especie')
especies_disp = ["Todas"] + sorted(df_exc_especie['Especie'].dropna().unique().tolist())
if st.session_state.especie_sel not in especies_disp: st.session_state.especie_sel = "Todas"
especie_sel = st.sidebar.selectbox("Especie Identificada", especies_disp, key='especie_sel')

df_exc_fecha = obtener_filtrado_excluyendo('fecha')
fechas_disp = ["Todas"] + df_exc_fecha['Fecha'].dropna().unique().tolist()
if st.session_state.fecha_sel not in fechas_disp: st.session_state.fecha_sel = "Todas"
fecha_sel = st.sidebar.selectbox("Fecha de Detección", fechas_disp, key='fecha_sel')

df_filtrado = df.copy()
if camara_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Camara'] == camara_sel]
if especie_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Especie'] == especie_sel]
if fecha_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Fecha'] == fecha_sel]

# --- KPIS ---
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

# --- GALERÍA VISUAL DIRECTA DE LAS ÚLTIMAS 10 IMÁGENES ---
st.subheader("📸 Galería de Fotogramas en Directo (Últimas 10 Coincidencias)")
st.markdown("Las imágenes se muestran automáticamente en pantalla al aplicar los filtros, sincronizadas al instante con el servidor.")

if not df_filtrado.empty:
    df_ultimas_10 = df_filtrado.head(10).reset_index(drop=True)
    st.info(f"Mostrando {len(df_ultimas_10)} fotogramas en pantalla (de un total de {len(df_filtrado)} registros filtrados).")
    
    cols = st.columns(2)
    for idx, (_, row) in enumerate(df_ultimas_10.iterrows()):
        img_name = row.get('Archivo_Imagen', '')
        camara = row.get('Camara', '')
        fecha = row.get('Fecha', '')
        hora = row.get('Hora', '')
        especie = row.get('Especie', '')
        deteccion = row.get('Detecciones', '')
        
        # Construir la ruta URL directa al archivo de imagen en GitHub
        img_url = f"{GITHUB_RAW_BASE}{img_name}" if img_name else ""
        
        with cols[idx % 2]:
            st.markdown(f"#### 🦅 {especie}")
            st.caption(f"📍 Estación: **{camara}** | 📅 Fecha: **{fecha} {hora}** | 🔍 YOLO: `{deteccion}`")
            if img_url:
                try:
                    st.image(img_url, use_container_width=True)
                except Exception:
                    st.warning(f"No se pudo cargar la imagen: `{img_name}` (comprueba que esté sincronizada en GitHub).")
            st.markdown("---")
else:
    st.warning("No hay registros que coincidan con la combinación de filtros seleccionada.")
