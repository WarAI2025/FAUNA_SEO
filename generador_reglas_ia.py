import pandas as pd
import json
import re
import os

CARPETA_CAPTURAS = r"C:\Users\mirip\OneDrive\Escritorio\animales_detectados"
CSV_PATH = os.path.join(CARPETA_CAPTURAS, "registro_detecciones.csv")
JSON_PATH = os.path.join(CARPETA_CAPTURAS, "falsos_positivos_dinamicos.json")
UMBRAL_RECHAZOS = 5  # Mínimo de veces que Gemini debe rechazar un artefacto para crear la regla

def extract_bbox(coord_str):
    if pd.isna(coord_str): return None
    m = re.search(r'\[(.*?)\]', str(coord_str))
    if m:
        try:
            return tuple([round(float(x), 3) for x in m.group(1).split(',')])
        except: return None
    return None

def extract_yolo_class(det_str):
    if pd.isna(det_str): return None
    m = re.match(r'([a-zA-Z]+)', str(det_str))
    return m.group(1).lower() if m else None

def actualizar_reglas_dinamicas():
    print("Iniciando análisis de IA para generación de reglas dinámicas...")
    if not os.path.exists(CSV_PATH):
        print("CSV de detecciones no encontrado.")
        return

    try:
        df = pd.read_csv(CSV_PATH, sep=';', encoding='utf-8', on_bad_lines='skip')
        df['bbox'] = df['Coordenadas_BBox'].apply(extract_bbox)
        df['yolo_class'] = df['Detecciones'].apply(extract_yolo_class)
        
        # Filtrar los registros que Gemini ha rechazado sistemáticamente
        rejections = df[df['Especie_Gemini'].str.lower().str.contains('sin animal|no identifica|artefacto|falso', na=False)]
        
        # Agrupar y contar las coordenadas idénticas por cámara y clase
        if not rejections.empty:
            rechazos_agrupados = rejections.groupby(['Camara', 'yolo_class', 'bbox']).size().reset_index(name='count')
            rechazos_agrupados = rechazos_agrupados[rechazos_agrupados['count'] >= UMBRAL_RECHAZOS]
            
            nuevas_reglas = {}
            for _, row in rechazos_agrupados.iterrows():
                cam = row['Camara']
                cls = row['yolo_class']
                cx, cy, w, h = row['bbox']
                
                # Crear un margen de tolerancia (±0.03) alrededor de la coordenada exacta
                margen = 0.03
                regla = {
                    "descripcion": f"Artefacto dinámico aprendido por IA ({row['count']} rechazos)",
                    "clases": [cls],
                    "limites": {
                        "cx": (max(0, cx - margen), min(1, cx + margen)),
                        "cy": (max(0, cy - margen), min(1, cy + margen)),
                        "w": (max(0, w - margen), min(1, w + margen)),
                        "h": (max(0, h - margen), min(1, h + margen))
                    }
                }
                
                if cam not in nuevas_reglas:
                    nuevas_reglas[cam] = []
                nuevas_reglas[cam].append(regla)
            
            # Guardar el JSON
            with open(JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(nuevas_reglas, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Se han generado {sum(len(v) for v in nuevas_reglas.values())} nuevas reglas dinámicas en {JSON_PATH}")
        else:
            print("No se encontraron suficientes rechazos de Gemini para generar nuevas reglas.")
            
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {e}")

if __name__ == "__main__":
    actualizar_reglas_dinamicas()
