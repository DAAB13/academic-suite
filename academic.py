import typer
from rich import print
from src.bot_blackboard import etl_bot
from src.bot_blackboard import mapa
from src.bot_blackboard import bot_scrapper
from src.operaciones import etl_ope
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl") 

app = typer.Typer(
    name="Academic Suite",
    help="Sistema de Orquestación Operativa y RPA para la UPN.",
    add_completion=False
)

# --- COMANDOS BLACKBOARD (RPA) ---
@app.command('bb-mapa')
def actualizar_mapa():
    """Ejecutar cuando tenga permisos de supervicion en nuevos programas. Actualiza la Base Maestra de IDs desde la API de Blackboard."""
    print("[bold magenta]🗺️  Iniciando actualización de Mapa de IDs...[/bold magenta]")
    mapa.run()
    print("[bold green]✅ Mapa sincronizado correctamente.[/bold green]")

@app.command('bb-etl')
def etl_blackboard():
    """Prepara (resumen_con_llave) de mis cursos 'activos' para el bot_scrapper en blackboard."""
    print("[bold yellow]⏳ Iniciando limpieza de datos ETL...[/bold yellow]")
    etl_bot.run()
    print("[bold green]✅ Combustible para el Bot listo.[/bold green]")

@app.command('bb-scrapper')
def bot_scrapper_blackboard():
    """Lanza el Robot RPA para extraer link de grabaciones (Chrome)."""
    # El mensaje de inicio ya lo maneja la tabla de pre-vuelo de vista_bot.py
    # así que aquí solo llamamos a la función.
    bot_scrapper.run()
    # El mensaje de fin también lo maneja el bot, así queda limpio.



# --- COMANDOS OPERACIONES (SUPERVISIÓN) ---
@app.command('ope-etl')
def etl_operaciones():
    """Genera la agenda de supervisión diaria y audita alertas."""
    print("[bold cyan]📅 Generando agenda operativa...[/bold cyan]")
    etl_ope.run()
    # La vista_diaria ya imprime el resultado final, no necesitamos print extra aquí

# --- PUNTO DE ENTRADA ---
if __name__ == "__main__":
    app()