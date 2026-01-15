import win32com.client as win32
import os
import pandas as pd
from rich.console import Console
from src.shared.config_loader import config, BASE_DIR

console = Console()

def excel_a_html(ruta_archivo):
    """Recibe la ruta, lee el Excel y lo convierte a HTML."""
    try:
        # Ya no verificamos aquí si existe, porque se lo pasamos desde la función principal
        df_completo = pd.read_excel(ruta_archivo)

        estilos = """
        <style>
            .excel-table { border-collapse: collapse; width: 100%; font-family: Calibri, sans-serif; font-size: 9pt; }
            .excel-table th { background-color: #2F5597; color: white; padding: 5px; border: 1px solid #ffffff; text-align: center; }
            .excel-table td { border: 1px solid #BFBFBF; padding: 4px; text-align: left; }
            .excel-table tr:nth-child(even) { background-color: #D9E1F2; }
        </style>
        """
        
        cuerpo_tabla = df_completo.to_html(index=False, classes='excel-table', border=0)
        return estilos + cuerpo_tabla
    except Exception as e:
        return f"<p style='color:red;'>Error al procesar el Excel: {str(e)}</p>"

def crear_borrador(contenido_cuerpo):
    """Crea el borrador unificando la ruta del archivo."""
    try:
        # 1. DEFINIMOS LA RUTA UNA SOLA VEZ
        ruta_final_excel = str(BASE_DIR / config['paths']['data'] / config['files']['reporte_domingo'])

        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0) # correo nuevo
        
        # Actualizado desde config.yaml
        mail.To = config['reporting']['recipient']
        mail.Subject = config['reporting']['subject']
        
        # 2. verificamos que exista para crear tabla html
        if os.path.exists(ruta_final_excel):
            tabla_desde_excel = excel_a_html(ruta_final_excel)
        else:
            tabla_desde_excel = "<p style='color:red;'>Error: No se encontró el archivo físico.</p>"

        mail.Display() # Mostramos el correo
        firma_cargada = mail.HTMLBody 
        
        # 3. ENSAMBLAJE DEL CUERPO (HTML)
        mail.HTMLBody = f"""
        <html>
            <body style="font-family: Calibri, sans-serif; font-size: 11pt;">
                {contenido_cuerpo.replace('\n', '<br>')}
                <br><br>
                <strong>Resumen de clases programadas de la semana</strong>
                <br><br>
                {tabla_desde_excel}
                <br><br>
                {firma_cargada}
            </body>
        </html>
        """
        # Guardamos en la carpeta de 'Borradores'
        mail.Save() 
        console.print("[bold green]✉️ Borrador generado correctamente con tabla incrustada.[/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error Crítico:[/bold red] {e}")