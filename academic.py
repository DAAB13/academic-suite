import typer
from datetime import datetime
from rich import print
from src.bot_blackboard import etl_bot, mapa, bot_scrapper
from src.operaciones import etl_ope
from src.reporte_semanal import incidencias, etl_sunday, agente_ia, outlook
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl") 

# --- APLICACIÓN PRINCIPAL ---
app = typer.Typer(
    name="Academic Suite",
    help="Sistema de Orquestación Operativa y RPA para la UPN.",
    add_completion=False,
    rich_markup_mode="rich"
)

# --- DEFINICIÓN DE SUB-MÓDULOS ---
# Creamos "carpetas" de comandos para organizar el tablero
bb_app = typer.Typer(help="🤖 BLACKBOARD (RPA)")
ope_app = typer.Typer(help="📅 OPERACIONES (Supervisión)")
reporte_app = typer.Typer(help="📧 REPORTE SEMANAL")

# Conectamos los sub-módulos a la aplicación principal
app.add_typer(bb_app, name="bb")
app.add_typer(ope_app, name="ope")
app.add_typer(reporte_app, name="repo")


# ==========================================
# 🤖 COMANDOS BLACKBOARD (RPA) -> Grupo 'bb'
# ==========================================

@bb_app.command('mapa')
def actualizar_mapa():
    """Ejecutar cuando tenga permisos de supervicion en nuevos programas. Actualiza la Base Maestra de IDs desde la API de Blackboard."""
    print("[bold magenta]🗺️  Iniciando actualización de Mapa de IDs...[/bold magenta]")
    mapa.run()
    print("[bold green]✅ Mapa sincronizado correctamente.[/bold green]")

@bb_app.command('etl')
def etl_blackboard():
    """Prepara (resumen_con_llave) de mis cursos 'activos' para el bot_scrapper en blackboard."""
    print("[bold yellow]⏳ Iniciando limpieza de datos ETL...[/bold yellow]")
    etl_bot.run()
    print("[bold green]✅ Combustible para el Bot listo.[/bold green]")

@bb_app.command('scrapper')
def bot_scrapper_blackboard():
    """Lanza el Robot RPA para extraer link de grabaciones (Chrome)."""
    # El mensaje de inicio ya lo maneja la tabla de pre-vuelo de vista_bot.py
    # así que aquí solo llamamos a la función.
    bot_scrapper.run()
    # El mensaje de fin también lo maneja el bot, así queda limpio.


# ==================================================
# 📅 COMANDOS OPERACIONES (SUPERVISIÓN) -> Grupo 'ope'
# ==================================================

@ope_app.command('etl')
def etl_operaciones():
    """Genera la agenda de supervisión diaria y audita alertas."""
    print("[bold cyan]📅 Generando agenda operativa...[/bold cyan]")
    etl_ope.run()
    # La vista_diaria ya imprime el resultado final, no necesitamos print extra aquí


# ===============================================
# 📧 REPORTE SEMANAL DOMINGOS -> Grupo 'reporte'
# ===============================================

@reporte_app.command('inc-log')
def registrar_incidencia(
    id_clase: str = typer.Option(..., "--id", help="ID único => Periodo.NRC"),
    motivo: str = typer.Option(..., help="Descripción de la incidencia"),
    # Mantenemos el default de hoy, pero si escribes --fecha DD/MM/AAAA lo sobreescribe
    fecha: str = typer.Option(datetime.now().strftime("%d/%m/%Y"), "--fecha", help="Fecha de la clase (DD/MM/YYYY)")
):
    """Anota una incidencia vinculada a un ID y una FECHA específica."""
    incidencias.registrar(id_clase, motivo, fecha)

@reporte_app.command('sunday')
def ejecutar_reporte_semanal():
    """[DOMINGOS] Procesa Panel V7 y redacta el correo con IA."""
    df_para_ia = etl_sunday.run()
    
    if df_para_ia is not None:
        # 1. Llamamos a la IA para redactar (esto ya lo tienes)
        texto_correo = agente_ia.redactar_correo(df_para_ia)
        
        print("\n[bold magenta]📝 BORRADOR DEL CORREO GENERADO:[/bold magenta]")
        print("-" * 50)
        print(texto_correo)
        print("-" * 50)
        
        # 2. ENVIAR A OUTLOOK
        
        outlook.crear_borrador(texto_correo, df_para_ia)
        
        print("\n[bold green]✔ Datos y redacción listos para enviar.[/bold green]")


if __name__ == "__main__":
    app()