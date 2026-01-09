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
    UPN_MAIL = os.getenv("UPN_MAIL")
    UPN_PASS = os.getenv("UPN_PASS")

    # Construcción dinámica
    ARCHIVO_SALIDA = BASE_DIR / config['paths']['data'] / config['files']['base_maestra_ids']
    
    # Crea la subcarpeta 'bot_blackboard' automáticamente si no existe
    ARCHIVO_SALIDA.parent.mkdir(parents=True, exist_ok=True)

    # Validación
    if not USER_ID_BB:
        console.print("[bold red]❌ ERROR: No se encontró USER_ID_BB en el archivo .env[/bold red]")
        return

    # ==========================================
    # 2. OBTENCIÓN DE COOKIES (PLAYWRIGHT AUTO-LOGIN)
    # ==========================================
    with sync_playwright() as p:
        console.print("[bold magenta]--- 🎭 INICIANDO AUTENTICACIÓN AUTOMÁTICA ---[/bold magenta]")
        
        # Lanzamos navegador
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # NAVEGACIÓN INICIAL
        page.goto("https://upn-colaborador.blackboard.com/")
        
        # LOGICA DE LOGIN AUTOMATICO
        if UPN_MAIL and UPN_PASS:
            try:
                # 1. Click en Supervisores (Si existe)
                btn_sup = page.locator("text=Supervisores")
                if btn_sup.is_visible():
                    btn_sup.click()

                # 2. Llenar credenciales (USANDO IDS PRECISOS DE UPN)
                try: 
                    # Definimos los selectores exactos de tu captura F12
                    selector_user = "input[id$='txtUserid']"
                    selector_pass = "input[id$='tbxPassword']"
                    selector_btn = "input[id$='btnSubmit']"

                    # Esperamos a que el campo de usuario aparezca
                    page.wait_for_selector(selector_user, timeout=10000)
                    
                    # Llenamos la información
                    page.locator(selector_user).fill(UPN_MAIL)
                    page.locator(selector_pass).fill(UPN_PASS)
                    
                    # Hacemos clic en el botón Enviar (que es un input, no un button)
                    page.locator(selector_btn).click()
                    console.print("[bold green]✔ Datos de acceso ingresados...[/bold green]")
                except Exception as e:
                    console.print(f"[yellow]⚠ No se detectó el formulario de login (quizás ya inició sesión): {e}[/yellow]")

                # 3. Manejo de MFA (Z Flip6)
                try:
                    # Selector exacto basado en tu F12 (id completo para evitar errores)
                    selector_mfa_btn = "input#ContentPlaceHolder1_MFALoginControl1_RegistrationMethodView_btnSubmit"
                    
                    console.print("[dim]⏳ Buscando botón de envío de MFA...[/dim]")
                    
                    # CORRECCIÓN: wait_for_selector SI espera a que aparezca el botón
                    page.wait_for_selector(selector_mfa_btn, state="visible", timeout=15000)
                    
                    # Un pequeño respiro de medio segundo para asegurar que el click sea efectivo
                    time.sleep(0.5) 
                    
                    console.print("[bold yellow]📱 Enviando solicitud de inicio a tu Z Flip6...[/bold yellow]")
                    page.locator(selector_mfa_btn).click()
                    
                    console.print("[bold cyan]📲 ¡Revisa tu teléfono ahora y dale a ACEPTAR![/bold cyan]")
                except Exception as e:
                    console.print(f"[dim]ℹ️ No se detectó el botón de MFA (quizás ya pasó): {e}[/dim]")
                    
                
                # 4. ESPERA INTELIGENTE DE ÉXITO
                console.print("[dim]⏳ Esperando acceso a Blackboard...[/dim]")
                try:
                    # Esperamos hasta 2 minutos (120000 ms) para que aceptes en el cel
                    page.wait_for_url("**/ultra/stream", timeout=120000)
                    console.print("[bold green]✅ Login Exitoso detectado.[/bold green]")
                except:
                    console.print("[bold red]❌ Tiempo de espera agotado o login fallido.[/bold red]")
                    browser.close()
                    return

            except Exception as e:
                console.print(f"[red]Error en flujo de login: {e}[/red]")
        else:
            console.print("[yellow]⚠️ Sin credenciales en .env. Login manual requerido.[/yellow]")
            input("👉 Presiona ENTER cuando hayas ingresado...")

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