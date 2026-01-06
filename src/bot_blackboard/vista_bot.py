from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import pandas as pd

console = Console()

def mostrar_tabla_prevuelo(df_input):
    """
    Muestra la lista de cursos que se van a procesar antes de iniciar el robot.
    Sirve para validar visualmente la carga de trabajo y las llaves internas.
    """
    count = len(df_input)
    console.print("\n[bold cyan]--- 🤖 BOT RPA: PREPARACIÓN DE VUELO ---[/bold cyan]")
    
    # Creamos una tabla elegante estilo "Magenta"
    table = Table(title=f"📦 CARGA DE TRABAJO: {count} CURSOS DETECTADOS", border_style="magenta", expand=True)
    
    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("ID (Periodo.NRC)", style="bold cyan", no_wrap=True)
    table.add_column("Curso", style="white")
    table.add_column("Llave Interna", justify="center")

    for idx, row in df_input.iterrows():
        # Recortamos el nombre si es muy largo para que la tabla no se rompa visualmente
        nombre = str(row.get('CURSO', 'N/A'))
        if len(nombre) > 50: nombre = nombre[:47] + "..."
        
        id_int = str(row.get('ID_Interno', ''))
        
        # Validación visual de la llave
        if id_int and id_int != 'nan':
            estado_llave = f"[green]{id_int}[/green]" 
        else:
            estado_llave = "[bold red]FALTA[/bold red]"

        table.add_row(
            str(idx + 1),
            str(row.get('ID', 'N/A')),
            nombre,
            estado_llave
        )

    console.print(table)
    console.print(f"[dim]Perfil de Chrome cargado. Esperando confirmación de inicio...[/dim]\n")

def log_curso_inicio(idx, total, id_curso, nombre_curso):
    """
    Abre una 'tarjeta' visual para el curso actual.
    """
    console.print(f"\n[bold magenta]╭── 🤖 PROCESANDO CURSO [{idx}/{total}]: {id_curso} ──╮[/bold magenta]")
    console.print(f"[bold magenta]│[/bold magenta] 🎓 [white]{nombre_curso}[/white]")

def log_accion(mensaje, icono="🔹", estilo="cyan"):
    """
    Log para acciones intermedias (clicks, navegación).
    """
    console.print(f"[bold magenta]│[/bold magenta]    {icono} [{estilo}]{mensaje}[/{estilo}]")

def log_exito(mensaje):
    """
    Log para acciones exitosas (Link capturado).
    """
    console.print(f"[bold magenta]│[/bold magenta]    [bold green]✅ {mensaje}[/bold green]")

def log_alerta(mensaje):
    """
    Log para advertencias (Carpeta vacía, pestaña no visible).
    """
    console.print(f"[bold magenta]│[/bold magenta]    [bold yellow]⚠️ {mensaje}[/bold yellow]")

def log_error(mensaje):
    """
    Log para errores críticos (Timeout, crash).
    """
    console.print(f"[bold magenta]│[/bold magenta]    [bold red]❌ {mensaje}[/bold red]")

def log_curso_fin():
    """
    Cierra la 'tarjeta' visual del curso.
    """
    console.print(f"[bold magenta]╰──────────────────────────────────────────────────╯[/bold magenta]")