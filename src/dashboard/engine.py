import pandas as pd
from datetime import datetime
from src.shared.config_loader import config, BASE_DIR

def contar_alertas():
  # BASE_DIR / "01_data" / "operaciones/reporte_alertas.csv"
  ruta_alertas = BASE_DIR / config['paths']['data'] / config['files']['reporte_alertas']

  # Pathlib nos permite verificar si el archivo existe
  if ruta_alertas.exists():
    try:
      df = pd.read_csv(ruta_alertas, sep=None, engine='python', encoding='latin-1')
      return len(df)
    except Exception as e:
      print(f"Error al leer el archivo: {e}")
      return 0
  return 0


def contar_clases_hoy():
  ruta_programacion = BASE_DIR / config['paths']['inputs'] / config['files']['programacion']
  if not ruta_programacion.exists(): return 0
  try:
    df = pd.read_excel(
      ruta_programacion, 
      sheet_name='PROGRAMACIÓN', 
      usecols=['FECHAS'], # <--- Solo lee lo necesario
      engine='openpyxl'
      )
    hoy = datetime.now().date()
    clases_hoy = df[pd.to_datetime(df['FECHAS']).dt.date == hoy]
    return len(clases_hoy)
  except Exception as e:
    print(f"error optimizado: {e}")
    return 0
