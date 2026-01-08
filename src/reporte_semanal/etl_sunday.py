import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box
from src.shared.excel_utils import copiar_archivo_onedrive
from src.shared.config_loader import config, BASE_DIR
import os

console = Console()

PATH_ONEDRIVE = Path(config['paths']['onedrive']) / config['files']['programacion']
PATH_INPUT_LOCAL = BASE_DIR / config['paths']['inputs'] / config['files']['programacion']
PATH_LOG = BASE_DIR / config['paths']['data'] / config['files']['incidencias_log']
PATH_OUTPUT = BASE_DIR / config['paths']['data'] / config['files']['reporte_domingo']

def run():
    console.rule("[bold cyan]🚀 INICIANDO ETL DOMINICAL[/bold cyan]")

    if not PATH_ONEDRIVE.exists():
        console.print(f"[bold red]❌ Error:[/bold red] No encuentro el archivo en OneDrive.")
        return None

    ruta_excel = copiar_archivo_onedrive(str(PATH_ONEDRIVE), str(PATH_INPUT_LOCAL))
    if not ruta_excel: return None

    try:
        with console.status("[bold yellow]⏳ Procesando datos de 'DIEGO'...[/bold yellow]", spinner="dots"):
            df = pd.read_excel(ruta_excel, sheet_name="PROGRAMACIÓN")
            df.columns = [str(c).strip().upper() for c in df.columns]

            # 1. Filtro de Soporte
            if 'SOPORTE' in df.columns:
                df = df[df['SOPORTE'] == 'DIEGO'].copy()
            
            # 2. Crear ID y Normalizar Fechas
            df['ID'] = df['PERIODO'].astype(str) + "." + df['NRC'].astype(str)
            df['FECHAS'] = pd.to_datetime(df['FECHAS'])
            
            # 3. Filtro de Semana Dinámico
            hoy = datetime.now()
            start_week = (hoy - timedelta(days=hoy.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            end_week = (start_week + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
            df_semana = df[(df['FECHAS'] >= start_week) & (df['FECHAS'] <= end_week)].copy()

    except Exception as e:
        console.print(f"[bold red]❌ Error en carga:[/bold red] {e}")
        return None

    # 4. EL MERGE (Llave Compuesta: ID + FECHA)
    if PATH_LOG.exists():
        df_log = pd.read_csv(PATH_LOG, dtype={'ID': str})
        df_log['FECHA_CLASE_DT'] = pd.to_datetime(df_log['FECHA_CLASE'], dayfirst=True)
        
        df_completo = pd.merge(
            df_semana, 
            df_log[['ID', 'FECHA_CLASE_DT', 'MOTIVO']], 
            left_on=['ID', 'FECHAS'], 
            right_on=['ID', 'FECHA_CLASE_DT'], 
            how='left'
        )
    else:
        df_completo = df_semana
        df_completo['MOTIVO'] = ""

    df_completo['MOTIVO'] = df_completo['MOTIVO'].fillna("")
    df_completo['ESTADO DE CLASE'] = df_completo['ESTADO DE CLASE'].fillna("PENDIENTE")

    # --- NUEVO: ORDENAMIENTO CRONOLÓGICO ---
    # Ordenamos por fecha antes de convertirla a texto
    df_completo = df_completo.sort_values(by='FECHAS', ascending=True)

    # 5. PREPARAR SALIDAS
    cols_sunday = ['PROGRAMA.1', 'CURSO', 'SESIÓN', 'PERIODO', 'NRC', 'FECHAS', 'HORARIO', 'DOCENTE', 'ESTADO DE CLASE']
    df_para_ia = df_completo[cols_sunday + ['ID', 'MOTIVO']].copy()

    # Excel Limpio para Wilbert (Formateamos fecha a string DESPUÉS de ordenar)
    df_visual = df_completo[cols_sunday].copy()
    df_visual['FECHAS'] = df_visual['FECHAS'].dt.strftime('%d/%m/%Y')

    PATH_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df_visual.to_excel(PATH_OUTPUT, index=False)
    
    console.print(f"[bold green]✅ Proceso Terminado.[/bold green] Cursos de Diego: [cyan]{len(df_completo)}[/cyan]")
    mostrar_resumen_critico(df_para_ia)
    return df_para_ia

def mostrar_resumen_critico(df):
    """Muestra solo lo que requiere tu atención (Incidencias o Pendientes)"""
    # Como df ya viene ordenado de la función run(), las alertas también lo estarán
    alertas = df[(df['MOTIVO'] != "") | (df['ESTADO DE CLASE'] == "PENDIENTE")].copy()
    
    table = Table(title=f"🚨 Resumen de Alertas (Diego)", box=box.HEAVY_EDGE)
    table.add_column("ID", style="cyan")
    table.add_column("Día", style="magenta")
    table.add_column("Estado", style="bold red")
    table.add_column("Motivo registrado", style="yellow")

    if alertas.empty:
        console.print("[bold green]✨ No hay incidencias esta semana. Todo bajo control.[/bold green]")
    else:
        for _, row in alertas.iterrows():
            table.add_row(
                row['ID'], 
                row['FECHAS'].strftime("%d/%m"), 
                str(row['ESTADO DE CLASE']), 
                str(row['MOTIVO'])
            )
        console.print(table)