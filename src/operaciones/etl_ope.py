import pandas as pd
import os
from datetime import datetime
from src.shared.excel_utils import copiar_archivo_onedrive, exportar_reporte_supervision
from src.operaciones.alertas_ope import auditar_anomalias
from src.operaciones.vista_diaria import vista_diaria_terminal

def run():
    # --- 1. CONFIGURACIÓN ---
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    DIR_INPUTS = os.path.join(BASE_DIR, "00_inputs")
    DIR_OUTPUTS_OPE = os.path.join(BASE_DIR, "02_outputs", "operaciones")
    os.makedirs(DIR_OUTPUTS_OPE, exist_ok=True)

    NOMBRE_ARCHIVO_PROG = "PANEL DE PROGRAMACIÓN V7.xlsx"
    RUTA_ORIGEN = fr"C:\Users\Diego AB\OneDrive - EduCorpPERU\POSGRADO-EPEC - Panel de Control Integrado\{NOMBRE_ARCHIVO_PROG}"
    RUTA_LOCAL = os.path.join(DIR_INPUTS, NOMBRE_ARCHIVO_PROG)
    
    ARCHIVO_SALIDA = os.path.join(DIR_OUTPUTS_OPE, "supervisar_hoy.xlsx")

    print("\n--- 📅 OPERACIONES: GENERANDO AGENDA DEL DÍA ---")

    # --- 2. CARGA DE DATOS ---
    ruta_lectura = copiar_archivo_onedrive(RUTA_ORIGEN, RUTA_LOCAL)
    if not ruta_lectura: return

    try:
        # CORRECCIÓN: header=0 para leer bien los títulos
        df = pd.read_excel(ruta_lectura, sheet_name='PROGRAMACIÓN', header=0, engine='openpyxl')
        
        # Seleccionamos todas las columnas que necesitas
        cols_necesarias = ['SOPORTE', 'CURSO', 'PERIODO', 'NRC', 'DOCENTE', 'SESIÓN', 'FECHAS', 'HORARIO', 'ESTADO DE CLASE']
        
        # Filtro de seguridad: Solo tomamos las que existen para no dar error
        df = df[[c for c in cols_necesarias if c in df.columns]].copy()

        # Filtro Usuario
        df = df[df['SOPORTE'].str.strip() == 'DIEGO'].copy()
        
        if df.empty:
            print("⚠️ No hay registros para DIEGO.")
            return

        # --- 3. LIMPIEZA Y FECHAS ---
        df['FECHAS'] = pd.to_datetime(df['FECHAS'], errors='coerce')
        
        df[['HORA_INI', 'HORA_FIN']] = df['HORARIO'].str.split(' - ', expand=True)
        df['HORA_INICIO'] = pd.to_datetime(df['HORA_INI'], format='%I:%M %p', errors='coerce').dt.time
        df['HORA_FIN'] = pd.to_datetime(df['HORA_FIN'], format='%I:%M %p', errors='coerce').dt.time
        
        # Crear ID (Periodo + NRC)
        df['ID'] = df['PERIODO'].astype(str) + '.' + df['NRC'].astype(str)

        # --- 4. FILTROS INTELIGENTES ---
        
        # A. Filtro de FECHA (La clave para limpiar lo antiguo)
        hoy = pd.Timestamp.now().normalize()
        df_futuro = df[df['FECHAS'] >= hoy].copy()
        
        # B. Filtro de AGENDA (Lo modificamos para que veas "Reprogramado")
        # Ya no usamos .isna() estricto, porque borraría los reprogramados.
        # Usamos df_futuro directamente. Esto te mostrará TODO lo que hay de hoy en adelante.
        df_agenda = df_futuro.copy()
        
        auditar_anomalias(df)
        vista_diaria_terminal(df_agenda)

        # --- 5. PREPARAR HOJAS ---
        
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
        df_resumen = df_futuro.groupby(['ID', 'CURSO', 'DOCENTE']).size().reset_index(name='Sesiones Restantes')

        # --- 6. EXPORTAR ---
        exito = exportar_reporte_supervision(df_operativa, df_resumen, ARCHIVO_SALIDA)
        
        if exito:
            print(f"✨ Archivo generado con {len(df_operativa)} filas en la agenda.")

    except Exception as e:
        print(f"❌ Error en Operaciones: {e}")

if __name__ == "__main__":
    run()