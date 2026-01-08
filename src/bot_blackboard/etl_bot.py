import pandas as pd
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from src.shared.excel_utils import copiar_archivo_onedrive
from src.shared.config_loader import config, BASE_DIR

# Inicializamos la consola de Rich
console = Console()

def run():
    # ==========================================
    # 1. CONFIGURACIÓN DE RUTAS
    # ==========================================
    
    # Carpetas principales
    DIR_INPUTS = BASE_DIR / config['paths']['inputs']
    DIR_DATA = BASE_DIR / config['paths']['data']

    # Archivos de entrada
    # Ahora esto apunta al CSV gracias a tu cambio en el YAML
    FILE_MAPA_IDS = DIR_DATA / config['files']['base_maestra_ids']
    NOMBRE_ARCHIVO_PROG = config['files']['programacion']
    
    # Construcción robusta path onedrive
    path_onedrive_base = Path(config['paths']['onedrive'])
    RUTA_ORIGEN_ONEDRIVE = path_onedrive_base / NOMBRE_ARCHIVO_PROG
    
    RUTA_TRABAJO_LOCAL = DIR_INPUTS / NOMBRE_ARCHIVO_PROG

    # Archivos de salida (Ahora será un CSV en bot_blackboard/)
    ARCHIVO_RESUMEN_LLAVE = DIR_DATA / config['files']['resumen_llave']

    # Aseguramos que la carpeta exista por si ejecutamos este script solo
    ARCHIVO_RESUMEN_LLAVE.parent.mkdir(parents=True, exist_ok=True)

    # ==========================================
    # 2. COPIA DE SEGURIDAD
    # ==========================================
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
        # El Panel de Programación SIGUE SIENDO EXCEL (eso no cambia)
        df_total = pd.read_excel(ruta_final_lectura, sheet_name='PROGRAMACIÓN', header=0, engine='openpyxl')

        columnas_interes = ['SOPORTE', 'CURSO', 'PERIODO', 'NRC', 'DOCENTE', 'ESTADO DE CLASE']
        cols_existentes = [c for c in columnas_interes if c in df_total.columns]
        df_seguimiento = df_total[cols_existentes].copy()

        # Generar ID único
        if 'PERIODO' in df_seguimiento.columns and 'NRC' in df_seguimiento.columns:
            df_seguimiento['ID'] = df_seguimiento['PERIODO'].astype(str) + '.' + df_seguimiento['NRC'].astype(str)

        # Filtrar por usuario
        if 'SOPORTE' in df_seguimiento.columns:
            df_diego = df_seguimiento[df_seguimiento['SOPORTE'].str.strip() == 'DIEGO'].copy()
        else:
            console.print("[bold red]⚠️ Advertencia: Columna SOPORTE no encontrada.[/bold red]")
            return

        if not df_diego.empty:
            df_estados = df_diego.groupby('ID')['ESTADO DE CLASE'].apply(
                lambda x: 'ACTIVO' if x.isna().any() else 'FINALIZADO'
            ).reset_index(name='ESTADO_CURSO')
            
            df_diego = pd.merge(df_diego, df_estados, on='ID', how='left')

            # --- CAMBIO IMPORTANTE: LECTURA DEL MAPA CSV ---
            if os.path.exists(FILE_MAPA_IDS):
                # Leemos CSV con punto y coma y latin1
                df_mapa = pd.read_csv(FILE_MAPA_IDS, sep=';', dtype={'ID': str}, encoding='latin1')
                
                df_activos = df_diego[df_diego['ESTADO_CURSO'] == 'ACTIVO'].copy()
                df_activos['ID'] = df_activos['ID'].astype(str)
                
                df_resumen = df_activos.groupby(['ID', 'CURSO', 'DOCENTE']).size().reset_index(name='Total Sesiones')

                # Cruzamos con el mapa
                df_final_bot = pd.merge(df_resumen, df_mapa[['ID', 'ID_Interno']], on='ID', how='left')
                
                # --- CAMBIO IMPORTANTE: EXPORTACIÓN A CSV ---
                # Guardamos como CSV en la nueva ruta
                df_final_bot.to_csv(ARCHIVO_RESUMEN_LLAVE, index=False, sep=';', encoding='latin1')
                
                cantidad_combustible = len(df_final_bot)
                
                mensaje_panel = f"""
    📊 [bold white]Resumen de Combustible Generado (CSV)[/bold white]
    
    🔹 [cyan]Registros Totales (Diego):[/cyan] {len(df_diego)}
    🔹 [cyan]Cursos Únicos Activos:[/cyan]  [bold white]{cantidad_combustible}[/bold white]
    
    💾 [dim]Guardado en: {config['paths']['data']}/{config['files']['resumen_llave']}[/dim]
    """
                estilo_borde = "green" if cantidad_combustible > 0 else "red"
                console.print(Panel(mensaje_panel, title="✅ ETL FINALIZADO", border_style=estilo_borde, expand=False))
                
            else:
                console.print(f"[bold red]❌ ERROR: No se encontró la base maestra CSV en {FILE_MAPA_IDS}[/bold red]")
                console.print("[yellow]💡 Sugerencia: Ejecuta 'python academic.py bb mapa' primero.[/yellow]")

        else:
            console.print("[bold yellow]⚠️ No se encontraron registros activos para 'DIEGO'.[/bold yellow]")

    except Exception as e:
        console.print(f"[bold red]❌ Error Crítico en ETL: {e}[/bold red]")

if __name__ == "__main__":
    run()