import pandas as pd
from datetime import datetime
from pathlib import Path
from rich.console import Console

console = Console()

# Configuración de Rutas
DATA_DIR = Path("01_data/reporte_semanal")
LOG_FILE = DATA_DIR / "incidencias_log.csv"

def registrar(id_clase: str, motivo: str, fecha_clase: str):
    try:
        # 1. Asegurar existencia de la carpeta
        DATA_DIR.mkdir(parents=True, exist_ok=True,)
        
        # 2. Estructura de datos (Sin DOCENTE para evitar redundancia)
        nueva_fila = {
            "FECHA_REGISTRO": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ID": id_clase,
            "FECHA_CLASE": fecha_clase,
            "MOTIVO": motivo
        }
        
        df = pd.DataFrame([nueva_fila])
        
        # 3. Guardar
        header = not LOG_FILE.exists()
        df.to_csv(LOG_FILE, mode='a', index=False, header=header, encoding='utf-8')
        
        console.print(f"[bold green]✔[/bold green] Incidencia guardada en bitácora para el ID: [yellow]{id_clase}[/yellow]")
        
    except Exception as e:
        console.print(f"[bold red]✘ Error al registrar incidencia:[/bold red] {e}")