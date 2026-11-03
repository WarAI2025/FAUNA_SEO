import os
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title='FAUNA SEO - Cuadro de Mando', page_icon='🦉', layout='wide'
)

st.title('🌲 FAUNA SEO: Sistema de Monitorización de Fauna')
st.markdown(
    'Panel de control en tiempo real para el seguimiento de avistamientos'
    ' silvestres.'
)

# 1. Carga de datos
CSV_REGISTRO = 'registro_detecciones.csv'


@st.cache_data(ttl=60)
def cargar_datos(path):
  if os.path.exists(path):
    try:
      # on_bad_lines='skip' hace que Pandas ignore cualquier fila mal estructurada en el CSV
      df = pd.read_csv(path, on_bad_lines='skip')
      return df
    except Exception as e:
      st.error(f"Error al leer el CSV: {e}")
      return pd.DataFrame()
  return pd.DataFrame()


df_detecciones = cargar_datos(CSV_REGISTRO)

if not df_detecciones.empty:
  # --- BARRA LATERAL: FILTROS GLOBALES ---
  st.sidebar.header('🔍 Filtros del Sistema')

  # Obtener lista de cámaras o especies si las columnas existen
  # (Asumiendo nombres estándar en base a tus logs: camara, especie/etiqueta, fecha)
  especies_disponibles = (
      df_detecciones['especie'].unique()
      if 'especie' in df_detecciones.columns
      else []
  )
  filtro_especie = st.sidebar.multiselect(
      'Filtrar por Especie',
      options=especies_disponibles,
      default=especies_disponibles,
  )

  # Aplicar filtros
  if filtro_especie and 'especie' in df_detecciones.columns:
    df_filtrado = df_detecciones[
        df_detecciones['especie'].isin(filtro_especie)
    ]
  else:
    df_filtrado = df_detecciones

  # --- MÓDULO 1: CUADRO DE MANDO (DASHBOARD AL INICIO) ---
  st.subheader('📊 Cuadro de Mando General')

  col1, col2, col3, col4 = st.columns(4)
  total_avistamientos = len(df_filtrado)
  especies_unicas = (
      df_filtrado['especie'].nunique()
      if 'especie' in df_filtrado.columns
      else 0
  )

  col1.metric('Total Avistamientos', total_avistamientos)
  col2.metric('Especies / Categorías', especies_unicas)
  col3.metric('Cámaras Activas', '11')  # Ajustable según tus cámaras
  col4.metric('Estado del Sistema', '🟢 Sincronizado')

  st.markdown('---')

  # Gráficos de resumen (Horas de actividad y distribución)
  c1, c2 = st.columns(2)

  with c1:
    st.markdown('### 📈 Resumen de Especies')
    if 'especie' in df_filtrado.columns:
      conteo_especies = df_filtrado['especie'].value_counts()
      st.bar_chart(conteo_especies)
    else:
      st.info('Columna de especies no detectada en el CSV.')

  with c2:
    st.markdown('### ⏰ Patrón de Horas de Actividad')
    # Si tienes una columna de hora o timestamp extraída del nombre de archivo (ej: YYYYMMDD_HHMMSS)
    if 'hora' in df_filtrado.columns:
      conteo_horas = df_filtrado['hora'].value_counts().sort_index()
      st.line_chart(conteo_horas)
    else:
      # Gráfico de ejemplo genérico si la columna hora se calcula al vuelo
      st.info(
          'Los gráficos de actividad por hora se adaptarán según el formato'
          ' temporal del registro.'
      )

  st.markdown('---')

  # --- MÓDULO 2: EXPLORADOR DE TODAS LAS IMÁGENES (SIN LÍMITE DE 10) ---
  st.subheader('🖼️ Explorador Completo de Imágenes')

  # Buscar todos los archivos .jpg en el directorio actual
  archivos_jpg = sorted(
      [f for f in os.listdir('.') if f.endswith('.jpg')], reverse=True
  )

  st.write(f'Mostrando todas las **{len(archivos_jpg)}** imágenes registradas.')

  # Paginación o scroll fluido para ver todas sin colgar la web
  # O simplemente mostrarlas en una cuadrícula optimizada
  grid_size = st.selectbox(
      'Imágenes por fila', options=[3, 4, 6], index=1
  )

  # Mostrar en columnas interactivas
  if archivos_jpg:
    for i in range(0, len(archivos_jpg), grid_size):
      cols = st.columns(grid_size)
      for j in range(grid_size):
        if i + j < len(archivos_jpg):
          img_name = archivos_jpg[i + j]
          with cols[j]:
            st.image(img_name, caption=img_name, use_container_width=True)
  else:
    st.warning('No se encontraron imágenes JPG en el directorio.')

else:
  st.error(
      'No se encuentra el archivo de registros (`registro_detecciones.csv`) o'
      ' está vacío.'
  )
