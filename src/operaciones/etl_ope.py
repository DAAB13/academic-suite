import pandas as pd
from pathlib import Path
import os
from datetime import datetime
from src.shared.excel_utils import copiar_archivo_onedrive, exportar_reporte_supervision
from src.operaciones.alertas_ope import auditar_anomalias
from src.operaciones.vista_diaria import vista_diaria_terminal
from src.shared.config_loader import config, BASE_DIR

def run():
    #-------------------------
    # CONFIGURACIÓN DE RUTAS
    #-------------------------
    RUTA_ORIGEN = Path(config['paths']['onedrive']) / config['files']['programacion']
    RUTA_LOCAL = BASE_DIR / config['paths']['inputs'] / config['files']['programacion']

    DIR_OUTPUTS_OPE = BASE_DIR / config['paths']['outputs'] / "operaciones"
    DIR_OUTPUTS_OPE.mkdir(parents=True, exist_ok=True) # Crea la carpeta si no existe

    ARCHIVO_SALIDA = BASE_DIR / config['paths']['outputs'] / config['files']['reporte_supervision']
    ARCHIVO_SALIDA.parent.mkdir(parents=True, exist_ok=True)

    print("\n--- 📅 OPERACIONES: GENERANDO AGENDA DEL DÍA ---")
    
    ruta_lectura = copiar_archivo_onedrive(str(RUTA_ORIGEN), str(RUTA_LOCAL))
    if not ruta_lectura: return

    try:
        df = pd.read_excel(ruta_lectura, sheet_name='PROGRAMACIÓN', header=0, engine='openpyxl')
        
        # Seleccionamos las columnas
        cols_necesarias = ['SOPORTE', 'CURSO', 'PERIODO', 'NRC', 'DOCENTE', 'SESIÓN', 'FECHAS', 'HORARIO', 'ESTADO DE CLASE']
        
        # Filtro de seguridad: Solo tomamos las que existen para no dar error
        df = df[[c for c in cols_necesarias if c in df.columns]].copy()

        # Filtro soporte 'DIEGO'
        df = df[df['SOPORTE'].str.strip() == 'DIEGO'].copy()
        
        if df.empty:
            print("⚠️ No hay registros para DIEGO.")
            return

        # LIMPIEZA Y FECHAS
        df['FECHAS'] = pd.to_datetime(df['FECHAS'], errors='coerce')
        
        # separamos en 2 columnas distintas
        df[['HORA_INI', 'HORA_FIN']] = df['HORARIO'].str.split(' - ', expand=True) # expand=True convierte el resultado directamente en nuevas columnas
        df['HORA_INICIO'] = pd.to_datetime(df['HORA_INI'], format='%I:%M %p', errors='coerce').dt.time
        df['HORA_FIN'] = pd.to_datetime(df['HORA_FIN'], format='%I:%M %p', errors='coerce').dt.time
        
        # crear ID (Periodo + NRC)
        df['ID'] = df['PERIODO'].astype(str) + '.' + df['NRC'].astype(str)

        # FILTROS INTELIGENTES
        # A. Filtro de FECHA normalize() elimina la hora y deja solo 00:00:00
        # Esto es vital para comparar el día de hoy sin que la hora actual interfiera.
        hoy = pd.Timestamp.now().normalize()
        df_futuro = df[df['FECHAS'] >= hoy].copy()
        
        # B. Filtro de AGENDA (Lo modificamos para que veas "Reprogramado")
        # # Mantenemos todo lo que es de hoy en adelante para tu agenda
        df_agenda = df_futuro.copy()
        
        # Llamamos a funciones externas para auditar errores y mostrar el resumen en consola
        auditar_anomalias(df)
        vista_diaria_terminal(df_agenda)

        # PREPARAR HOJAS        
        # Hoja 1: OPERATIVO (Con tus columnas exactas)
        df_operativa = df_agenda.sort_values(by=['FECHAS', 'HORA_INICIO'])
        
        cols_finales = [
            'SOPORTE', 'CURSO', 'DOCENTE', 'PERIODO', 'NRC', 'ID', 
            'SESIÓN', 'FECHAS', 'HORA_INICIO', 'HORA_FIN', 'ESTADO DE CLASE'
        ]
        
        # Filtro de seguridad por si alguna columna no se generó
        cols_a_exportar = [c for c in cols_finales if c in df_operativa.columns]
        df_operativa = df_operativa[cols_a_exportar]

        # Hoja 2: RESUMEN (Foto global)
        # groupby agrupa las filas y .size() cuenta cuántas sesiones quedan por curso
        df_resumen = df_futuro.groupby(['ID', 'CURSO', 'DOCENTE']).size().reset_index(name='Sesiones Restantes')

        # EXPORTAR
        exito = exportar_reporte_supervision(df_operativa, df_resumen, str(ARCHIVO_SALIDA))
        
        if exito:
            print(f"✨ Archivo generado con {len(df_operativa)} filas en la agenda.")

    except Exception as e:
        print(f"❌ Error en Operaciones: {e}")

if __name__ == "__main__":
    run()