import os
import re
import pandas as pd
import requests
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from pathlib import Path
from src.shared.config_loader import config, BASE_DIR
# IMPORTACIONES RICH
from rich.console import Console
from rich.panel import Panel

console = Console()

def run():
    # ==========================================
    # 1. CONFIGURACIÓN DE RUTAS
    # ==========================================
    # Carga las variables
    load_dotenv(os.path.join(BASE_DIR, ".env")) 
    USER_ID_BB = os.getenv("USER_ID_BB")

    # Construcción dinámica: academic-suite/ + 01_data/ + bot_blackboard/base_maestra_ids.csv
    ARCHIVO_SALIDA = BASE_DIR / config['paths']['data'] / config['files']['base_maestra_ids']
    
    # Crea la subcarpeta 'bot_blackboard' automáticamente si no existe
    ARCHIVO_SALIDA.parent.mkdir(parents=True, exist_ok=True)

    # Validación
    if not USER_ID_BB:
        console.print("[bold red]❌ ERROR: No se encontró USER_ID_BB en el archivo .env[/bold red]")
        return

    # ==========================================
    # 2. OBTENCIÓN DE COOKIES (PLAYWRIGHT)
    # ==========================================
    with sync_playwright() as p:
        console.print("[bold magenta]--- 🎭 INICIANDO SESIÓN MANUAL ---[/bold magenta]")
        
        # Lanzamos navegador
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://upn-colaborador.blackboard.com/")
        
        console.print("\n[bold yellow]🔑 ACCIÓN REQUERIDA:[/bold yellow] Realiza el Login en la ventana de Chrome.")
        input("👉 Cuando veas tus cursos, presiona ENTER aquí para capturar la llave... ")

        # Extraemos cookies
        cookies = context.cookies()
        cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        browser.close()

    # ==========================================
    # 3. CONSUMO DE API (REQUESTS CON RICH)
    # ==========================================
    # Aquí usamos el Spinner para que la espera se vea pro
    url = f"https://upn.blackboard.com/learn/api/v1/users/{USER_ID_BB}/memberships?expand=course.effectiveAvailability,course.permissions,courseRole&includeCount=true&limit=10000"
    
    headers = {
        "Cookie": cookie_string,
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }

    try:
        # Spinner "earth" (🌍) girando mientras descarga
        with console.status("[bold cyan]📡 Descargando mapa de cursos desde la Nube...[/bold cyan]", spinner="earth"):
            response = requests.get(url, headers=headers)
            # Un pequeño sleep para que alcances a ver la animación (opcional, pero se ve bien)
            time.sleep(1) 
        
        if response.status_code == 200:
            data = response.json()
            lista_cursos = []

            for item in data.get('results', []):
                curso_obj = item.get('course', {})
                nombre_full = curso_obj.get('name', '')
                
                # Buscamos el ID formato 123456.1234
                match = re.search(r'(\d{6}\.\d{4})', nombre_full)
                id_limpio = match.group(1) if match else "N/A"

                lista_cursos.append({
                    "ID": id_limpio,
                    "Nombre": nombre_full,
                    "ID_Interno": curso_obj.get('id'),
                    "ID_Visible": curso_obj.get('courseId')
                })

            df = pd.DataFrame(lista_cursos)
            df = df[["ID", "Nombre", "ID_Interno", "ID_Visible"]]

            # ==========================================
            # 4. EXPORTACIÓN
            # ==========================================
            df.to_csv(ARCHIVO_SALIDA, index=False, sep=';', encoding='latin1')
            
            # Panel de Éxito
            mensaje_final = f"""
    🗺️  [bold white]Base Maestra Generada[/bold white]
    
    🔹 [cyan]Cursos Mapeados:[/cyan] {len(df)}
    🔹 [cyan]Usuario ID:[/cyan] {USER_ID_BB}
    
    💾 [dim]Guardado en: 01_data/base_maestra_ids.xlsx[/dim]
            """
            console.print(Panel(mensaje_final, title="✅ MAPA SINCRONIZADO", border_style="green"))

        else:
            console.print(f"[bold red]❌ Error API: {response.status_code} - No autorizado o enlace roto.[/bold red]")
            
    except Exception as e:
        console.print(f"[bold red]❌ Error crítico en el proceso de mapa: {e}[/bold red]")

if __name__ == "__main__":
    run()