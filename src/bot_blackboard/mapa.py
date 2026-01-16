import os
import re
import pandas as pd
import requests
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from pathlib import Path
from src.shared.config_loader import config, BASE_DIR
from rich.console import Console
from rich.panel import Panel

console = Console()

def run():
    # ==========================================
    # 1. CONFIGURACIÓN Y CREDENCIALES
    # ==========================================
    load_dotenv(BASE_DIR / ".env") 
    USER_ID_BB = os.getenv("USER_ID_BB")
    UPN_MAIL = os.getenv("UPN_MAIL")
    UPN_PASS = os.getenv("UPN_PASS")

    # Rutas dinámicas para archivos
    ARCHIVO_SALIDA = BASE_DIR / config['paths']['data'] / config['files']['base_maestra_ids']
    ARCHIVO_SALIDA.parent.mkdir(parents=True, exist_ok=True)

    # --- NUEVO: Extraemos URLs y Selectores desde el YAML ---
    BB_URLS = config['blackboard']['urls']
    BB_SELECTORS = config['blackboard']['selectors']

    if not USER_ID_BB:
        console.print("[bold red]❌ ERROR: USER_ID_BB no encontrado en .env[/bold red]")
        return

    # ==========================================
    # 2. AUTENTICACIÓN (PLAYWRIGHT)
    # ==========================================
    with sync_playwright() as p:
        console.print("[bold magenta]--- 🎭 INICIANDO AUTENTICACIÓN ---[/bold magenta]")
        
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Usamos la URL desde el YAML
        page.goto(BB_URLS['login'])
        
        if UPN_MAIL and UPN_PASS:
            try:
                btn_sup = page.locator("text=Supervisores")
                if btn_sup.is_visible():
                    btn_sup.click()

                # --- USANDO SELECTORES DESDE EL YAML ---
                # Esperamos al cuadro de usuario
                page.wait_for_selector(BB_SELECTORS['user_input'], timeout=10000)
                
                # Llenamos credenciales usando los nombres guardados en el config
                page.locator(BB_SELECTORS['user_input']).fill(UPN_MAIL)
                page.locator(BB_SELECTORS['pass_input']).fill(UPN_PASS)
                page.locator(BB_SELECTORS['login_btn']).click()
                
                console.print("[bold green]✔ Credenciales ingresadas...[/bold green]")

                # --- MANEJO DE MFA (Z Flip6) ---
                try:
                    # Buscamos el botón de MFA usando la ruta guardada en el YAML
                    sel_mfa = BB_SELECTORS['mfa_submit']
                    page.wait_for_selector(sel_mfa, state="visible", timeout=15000)
                    
                    time.sleep(0.5) 
                    console.print("[bold yellow]📱 Enviando notificación push...[/bold yellow]")
                    page.locator(sel_mfa).click()
                    console.print("[bold cyan]📲 ¡Acepta en tu celular![/bold cyan]")
                except Exception:
                    console.print("[dim]ℹ️ No se requirió MFA o el botón no apareció.[/dim]")
                
                # Espera a que la URL cambie para confirmar éxito
                page.wait_for_url("**/ultra/stream", timeout=120000)
                console.print("[bold green]✅ Acceso concedido.[/bold green]")

            except Exception as e:
                console.print(f"[red]Error en login: {e}[/red]")
                browser.close()
                return

        # Capturamos las cookies para la API
        cookies = context.cookies()
        cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        browser.close()

    # ==========================================
    # 3. CONSUMO DE API (REQUESTS)
    # ==========================================
    # --- CONSTRUCCIÓN DINÁMICA DE LA URL ---
    # Usamos .format() para meter tu USER_ID_BB dentro del hueco {user_id} del YAML
    url_api = BB_URLS['api_memberships'].format(user_id=USER_ID_BB)
    
    headers = {
        "Cookie": cookie_string,
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }

    try:
        with console.status("[bold cyan]📡 Descargando mapa de cursos...", spinner="earth"):
            response = requests.get(url_api, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            lista_cursos = []

            for item in data.get('results', []):
                curso_obj = item.get('course', {})
                nombre_full = curso_obj.get('name', '')
                
                # REGEX: Busca el patrón NRC (6 dígitos . 4 dígitos)
                match = re.search(r'(\d{6}\.\d{4})', nombre_full)
                id_limpio = match.group(1) if match else "N/A"

                lista_cursos.append({
                    "ID": id_limpio,
                    "Nombre": nombre_full,
                    "ID_Interno": curso_obj.get('id'),
                    "ID_Visible": curso_obj.get('courseId')
                })

            df = pd.DataFrame(lista_cursos)
            
            # Guardamos el CSV con el separador oficial de tu configuración
            df.to_csv(
                ARCHIVO_SALIDA, 
                index=False, 
                sep=config['files']['separador_alertas_csv'], 
                encoding='latin1'
            )
            
            # Resumen visual final
            console.print(Panel(f"🔹 Cursos: {len(df)}\n💾 Guardado en: {ARCHIVO_SALIDA.name}", 
                            title="✅ MAPA ACTUALIZADO", border_style="green"))
    except Exception as e:
        console.print(f"[bold red]❌ Error en API: {e}[/bold red]")