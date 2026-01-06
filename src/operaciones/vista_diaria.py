from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import timedelta
import pandas as pd

console = Console()

def vista_diaria_terminal(df_agenda):
    """
    Muestra en la terminal EXACTAMENTE lo que Diego necesita:
    1. Conteo simple de hoy, mañana y pasado.
    2. Tabla completa de la agenda de hoy.
    """
    hoy = pd.Timestamp.now().normalize()
    manana = hoy + timedelta(days=1)
    pasado = hoy + timedelta(days=2)

    # --- 1. CÁLCULOS EXACTOS ---
    # Filtramos el DataFrame para contar
    count_hoy = len(df_agenda[df_agenda['FECHAS'] == hoy])
    count_manana = len(df_agenda[df_agenda['FECHAS'] == manana])
    count_pasado = len(df_agenda[df_agenda['FECHAS'] == pasado])

    # --- 2. IMPRIMIR LOS MENSAJES (Sin ruido) ---
    console.print("\n[bold cyan]--- 📅 RESUMEN DE CARGA ---[/bold cyan]")
    
    # Mensajes personalizados con fechas reales
    console.print(f"📌 [bold white]{count_hoy}[/bold white] sesiones a supervisar [green]HOY ({hoy.strftime('%d/%m')})[/green]")
    console.print(f"🔮 [bold white]{count_manana}[/bold white] sesiones a supervisar MAÑANA {manana.strftime('%d/%m')}")
    console.print(f"🔭 [bold white]{count_pasado}[/bold white] sesiones a supervisar PASADO {pasado.strftime('%d/%m')}")

    # --- 3. TABLA DETALLADA DE HOY (Todas las filas) ---
    df_hoy = df_agenda[df_agenda['FECHAS'] == hoy].sort_values(by='HORA_INICIO')

    if not df_hoy.empty:
        # Creamos la tabla visual
        table = Table(title=f"🚀 AGENDA COMPLETA HOY ({hoy.strftime('%d/%m')})", expand=True, border_style="green")
        
        table.add_column("Hora", style="cyan", no_wrap=True)
        table.add_column("ID", style="bold magenta")
        table.add_column("Curso", style="white")
        table.add_column("Docente", style="white")
        table.add_column("Estado", justify="center")

        for _, row in df_hoy.iterrows():
            # Formateo visual de la hora
            hora_str = row['HORA_INICIO'].strftime('%I:%M %p')
            
            # Lógica para mostrar estado (Vacío = Pendiente)
            estado_val = str(row['ESTADO DE CLASE']) if pd.notna(row['ESTADO DE CLASE']) else "Pendiente"
            
            # Color del estado: Rojo si es Reprogramado, Verde si es Pendiente
            if "REPROGRMADA" in estado_val:
                estilo_estado = "[bold red]"
            elif "Pendiente" in estado_val:
                estilo_estado = "[bold green]"
            else:
                estilo_estado = "[yellow]" # Para "Supervisado" u otros

            table.add_row(
                hora_str,
                str(row['ID']),
                str(row['CURSO'])[:35], # Recortamos un poco si es muy largo
                str(row['DOCENTE']),
                f"{estilo_estado}{estado_val}[/]"
            )
        
        console.print(table)
    else:
        console.print("\n[bold green]😎 ¡Hoy estás libre! No hay supervisiones para hoy.[/bold green]")