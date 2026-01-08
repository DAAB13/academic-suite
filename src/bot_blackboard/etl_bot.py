import pandas as pd
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from src.shared.excel_utils import copiar_archivo_onedrive
from src.shared.config_loader import config, BASE_DIR
from src.shared.config_loader import config

# Inicializamos la consola de Rich
console = Console()

def run():
    # ==========================================
    # 1. CONFIGURACIÓN DE RUTAS (INTACTA)
    # ==========================================
    # ==========================================
    # 1. CONFIGURACIÓN DE RUTAS (REFÁCTORIZADO)
    # ==========================================
    
    # Carpetas principales (paths relatives to BASE_DIR from config_loader)
    DIR_INPUTS = BASE_DIR / config['paths']['inputs']
    DIR_DATA = BASE_DIR / config['paths']['data']

    # Archivos de entrada
    FILE_MAPA_IDS = DIR_DATA / config['files']['base_maestra_ids']
    NOMBRE_ARCHIVO_PROG = config['files']['programacion']
    
    # Construcción robusta path onedrive
    path_onedrive_base = Path(config['paths']['onedrive'])
    RUTA_ORIGEN_ONEDRIVE = path_onedrive_base / NOMBRE_ARCHIVO_PROG
    
    RUTA_TRABAJO_LOCAL = DIR_INPUTS / NOMBRE_ARCHIVO_PROG

    # Archivos de salida
    ARCHIVO_RESUMEN_LLAVE = DIR_DATA / config['files']['resumen_llave']

    # ==========================================
    # 2. COPIA DE SEGURIDAD (CON VISUALIZACIÓN RICH)
    # ==========================================
    # Usamos un Spinner (relojito) para indicar que está trabajando
    with console.status("[bold cyan]🔄 Sincronizando panel desde OneDrive...[/bold cyan]", spinner="dots"):
        ruta_final_lectura = copiar_archivo_onedrive(RUTA_ORIGEN_ONEDRIVE, RUTA_TRABAJO_LOCAL)

    if not ruta_final_lectura:
        console.print("[bold red]❌ Error: No se pudo obtener el archivo origen.[/bold red]")
        return 

    # ==========================================
    # 3. LÓGICA DE PROCESAMIENTO
    # ==========================================
    console.print("[dim]⚙️  Procesando datos y filtrando usuario...[/dim]")

    try:
        df_total = pd.read_excel(ruta_final_lectura, sheet_name='PROGRAMACIÓN', header=0, engine='openpyxl')

        # Columnas necesarias
        columnas_interes = ['SOPORTE', 'CURSO', 'PERIODO', 'NRC', 'DOCENTE', 'ESTADO DE CLASE']
        cols_existentes = [c for c in columnas_interes if c in df_total.columns]
        df_seguimiento = df_total[cols_existentes].copy()

        # Generar ID único
        if 'PERIODO' in df_seguimiento.columns and 'NRC' in df_seguimiento.columns:
            df_seguimiento['ID'] = df_seguimiento['PERIODO'].astype(str) + '.' + df_seguimiento['NRC'].astype(str)

        # Filtrar por tu usuario 'DIEGO'
        if 'SOPORTE' in df_seguimiento.columns:
            df_diego = df_seguimiento[df_seguimiento['SOPORTE'].str.strip() == 'DIEGO'].copy()
        else:
            console.print("[bold red]⚠️ Advertencia: Columna SOPORTE no encontrada.[/bold red]")
            return

        if not df_diego.empty:
            # Determinar estado ACTIVO/FINALIZADO
            df_estados = df_diego.groupby('ID')['ESTADO DE CLASE'].apply(
                lambda x: 'ACTIVO' if x.isna().any() else 'FINALIZADO'
            ).reset_index(name='ESTADO_CURSO')
            
            df_diego = pd.merge(df_diego, df_estados, on='ID', how='left')

            # --- FILTRADO FINAL PARA EL BOT ---
            if os.path.exists(FILE_MAPA_IDS):
                df_mapa = pd.read_excel(FILE_MAPA_IDS, sheet_name='Mapa', dtype={'ID': str})
                
                # Solo cursos ACTIVO
                df_activos = df_diego[df_diego['ESTADO_CURSO'] == 'ACTIVO'].copy()
                df_activos['ID'] = df_activos['ID'].astype(str)
                
                # Resumen único por curso
                df_resumen = df_activos.groupby(['ID', 'CURSO', 'DOCENTE']).size().reset_index(name='Total Sesiones')

                # Cruzamos con el mapa de IDs
                df_final_bot = pd.merge(df_resumen, df_mapa[['ID', 'ID_Interno']], on='ID', how='left')
                
                # Exportar el "combustible"
                df_final_bot.to_excel(ARCHIVO_RESUMEN_LLAVE, index=False)
                
                # --- AQUÍ ESTÁ EL CAMBIO VISUAL (Reporte de Calidad) ---
                cantidad_combustible = len(df_final_bot)
                
                mensaje_panel = f"""
    📊 [bold white]Resumen de Combustible Generado[/bold white]
    
    🔹 [cyan]Registros Totales (Diego):[/cyan] {len(df_diego)}
    🔹 [cyan]Cursos Únicos Activos:[/cyan]  [bold white]{cantidad_combustible}[/bold white]
    
    💾 [dim]Archivo guardado en: 01_data/resumen_con_llave.xlsx[/dim]
    """
                estilo_borde = "green" if cantidad_combustible > 0 else "red"
                console.print(Panel(mensaje_panel, title="✅ ETL FINALIZADO", border_style=estilo_borde, expand=False))
                
            else:
                console.print(f"[bold red]❌ ERROR: No se encontró la base maestra en {FILE_MAPA_IDS}[/bold red]")
                console.print("[yellow]💡 Sugerencia: Ejecuta 'python main.py bb-mapa' primero.[/yellow]")

        else:
            console.print("[bold yellow]⚠️ No se encontraron registros activos para 'DIEGO'.[/bold yellow]")

    except Exception as e:
        console.print(f"[bold red]❌ Error Crítico en ETL: {e}[/bold red]")

if __name__ == "__main__":
    run()