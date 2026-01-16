import os
import pandas as pd
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv 
from pathlib import Path
# Importamos la configuración centralizada
from src.shared.config_loader import config, BASE_DIR
# Asumimos que vista_bot está en la misma carpeta o accesible
from src.bot_blackboard import vista_bot as vista 

def gestionar_login_upn(page, user_mail, user_pass):
    """
    Función robusta que maneja el flujo de Login de UPN/Laureate.
    """
    vista.log_accion("Verificando estado de sesión...", icono="🔐")
    
    # --- REFACTORIZADO: URL DESDE YAML ---
    url_login = config['blackboard']['urls']['login']
    
    try:
        page.goto(url_login, wait_until="domcontentloaded")
        time.sleep(3) 
    except:
        pass

    # CASO 1: Ya estamos dentro
    if "ultra" in page.url or "stream" in page.url:
        vista.log_exito("Sesión recuperada (Cookies válidas)")
        return True

    # CASO 2: Estamos en la portada (Requiere Login)
    btn_supervisores = page.locator("text=Supervisores")
    
    if btn_supervisores.is_visible():
        vista.log_accion("Iniciando Login Automático...", icono="🤖")
        btn_supervisores.click()
        
        # --- FASE 1: INGRESAR CREDENCIALES (SELECTORES DESDE YAML) ---
        try:
            # Usamos los selectores definidos en la sección 'blackboard' del config.yaml
            sel = config['blackboard']['selectors']
            
            # Esperamos explícitamente a que aparezca el campo de usuario
            page.wait_for_selector(sel['user_input'], timeout=10000)
            
            # Llenamos datos
            page.locator(sel['user_input']).fill(user_mail)
            page.locator(sel['pass_input']).fill(user_pass)
            
            # Click en Enviar
            page.locator(sel['login_btn']).click()
            vista.log_accion("Credenciales enviadas...", icono="📨")
            
            # --- FASE 2: MANEJO DE MFA (Z FLIP6) ---
            # Selector desde YAML
            selector_mfa_btn = sel['mfa_submit']
            
            vista.log_alerta("Buscando botón de confirmación MFA...")
            
            try:
                page.wait_for_selector(selector_mfa_btn, state="visible", timeout=15000)
                time.sleep(0.5) 
                
                vista.log_accion("Enviando solicitud al celular...", icono="📱")
                page.locator(selector_mfa_btn).click()
                
                vista.log_alerta("¡ACCIÓN REQUERIDA! Acepta en tu Z Flip6 ahora.")
            except:
                vista.log_accion("No se requirió clic en MFA o ya pasó.", icono="ℹ️")

            # --- FASE 3: ESPERAR ACCESO FINAL ---
            page.wait_for_url("**/ultra/stream", timeout=120000)
            vista.log_exito("Acceso autorizado detectado.")
            return True
            
        except Exception as e:
            vista.log_error(f"Fallo en proceso de login: {e}")
            return False
            
    return True

def run():
    # ==========================================
    # CONFIGURACIÓN (Rutas conectadas al YAML)
    # ==========================================
    # Cargamos credenciales usando Pathlib para la ruta del .env
    load_dotenv(BASE_DIR / ".env") 
    UPN_MAIL = os.getenv("UPN_MAIL")
    UPN_PASS = os.getenv("UPN_PASS")

    # --- REFACTORIZADO: RUTAS USANDO EL OPERADOR / DE PATHLIB ---
    # INPUT: 01_data / bot_blackboard / resumen_con_llave.csv
    INPUT_FILE = BASE_DIR / config['paths']['data'] / config['files']['resumen_llave']
    
    # OUTPUT: 02_outputs / bot_blackboard / reporte_grabaciones.xlsx
    OUTPUT_FILE = BASE_DIR / config['paths']['outputs'] / config['files']['reporte_grabaciones']
    
    # Perfil de Chrome (Guardado en 00_inputs/chrome_profile)
    USER_DATA_DIR = BASE_DIR / config['paths']['inputs'] / "chrome_profile"

    # Creación de Carpetas de Seguridad
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True) 
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Mapeo de meses (Mantenido igual)
    MESES_EN = {
        "January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06",
        "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12"
    }

    # --- FUNCIONES HELPER (INTACTAS) ---
    def parsear_fecha_compleja(texto_raw):
        fecha_fmt, inicio_fmt, fin_fmt = texto_raw, "", ""
        texto_limpio = texto_raw.replace("\n", " ").replace("\r", " ").strip()
        try:
            match_fecha = re.search(r'([A-Za-z]+)\s+(\d+)(?:st|nd|rd|th)?,\s+(\d{4})', texto_limpio)
            if match_fecha:
                mes_txt, dia, anio = match_fecha.groups()
                mes_num = MESES_EN.get(mes_txt, "01")
                fecha_fmt = f"{int(dia):02d}/{mes_num}/{anio}"
            
            patron_hora = r'(\d{1,2}:\d{2}\s*[APap][Mm])'
            horas_encontradas = re.findall(patron_hora, texto_limpio, re.IGNORECASE)
            
            if len(horas_encontradas) >= 1:
                hora_raw = horas_encontradas[0].upper().replace(".", "").replace(" ", "")
                if "PM" in hora_raw: hora_raw = hora_raw.replace("PM", " PM")
                if "AM" in hora_raw: hora_raw = hora_raw.replace("AM", " AM")
                try:
                    dt_ini = datetime.strptime(hora_raw.strip(), "%I:%M %p")
                    inicio_fmt = dt_ini.strftime("%H:%M")
                except: pass
            
            if len(horas_encontradas) >= 2:
                hora_raw = horas_encontradas[1].upper().replace(".", "").replace(" ", "")
                if "PM" in hora_raw: hora_raw = hora_raw.replace("PM", " PM")
                if "AM" in hora_raw: hora_raw = hora_raw.replace("AM", " AM")
                try:
                    dt_ini = datetime.strptime(hora_raw.strip(), "%I:%M %p")
                    fin_fmt = dt_ini.strftime("%H:%M")
                except: pass
        except Exception: pass
        return fecha_fmt, inicio_fmt, fin_fmt

    def limpiar_portapapeles(page):
        try: page.evaluate("navigator.clipboard.writeText('')")
        except: pass

    def leer_portapapeles(page):
        try: return page.evaluate("navigator.clipboard.readText()")
        except: return None

    def navegar_robusto(page, url):
        try:
            try: page.locator("button[title='Cerrar']").click(timeout=1000)
            except: pass
            page.goto(url, wait_until="networkidle", timeout=60000)
        except Exception:
            page.goto(url, wait_until="domcontentloaded")

    # ==========================================
    # LÓGICA PRINCIPAL
    # ==========================================
    if not INPUT_FILE.exists():
        print(f"❌ Error: Falta {INPUT_FILE}")
        print("💡 Ejecuta 'python academic.py bb etl' primero.")
        return

    # LECTURA DEL CSV INTERMEDIO
    df_input = pd.read_csv(INPUT_FILE, sep=';', dtype={'ID': str}, encoding='latin1')
    
    all_recordings = []
    vista.mostrar_tabla_prevuelo(df_input)

    with sync_playwright() as p:
        try:
            # Lanzamos Chrome con un perfil persistente para no loguearnos cada vez si es posible
            browser_context = p.chromium.launch_persistent_context(
                user_data_dir=str(USER_DATA_DIR),
                headless=False,
                channel="chrome", 
                args=["--start-maximized", "--disable-web-security"],
                permissions=["clipboard-read", "clipboard-write"]
            )
        except Exception as e:
            print(f"❌ Error lanzando Chrome: {e}")
            return

        page = browser_context.pages[0]

        # --- LOGIN AUTOMÁTICO ---
        if not UPN_MAIL or not UPN_PASS:
            print("⚠️ Faltan credenciales en .env. Pasando a modo manual...")
            page.goto(config['blackboard']['urls']['login'])
            input("👉 LOGUEATE, ESPERA A VER TUS CURSOS Y PRESIONA ENTER... ")
        else:
            login_exitoso = gestionar_login_upn(page, UPN_MAIL, UPN_PASS)
            if not login_exitoso:
                print("❌ Fallo crítico en login. Abortando.")
                browser_context.close()
                return

        time.sleep(2)

        for index, row in df_input.iterrows():
            id_curso_visible = row.get('ID', 'SinID')
            id_interno = row.get('ID_Interno')
            nombre_curso = row.get('CURSO', 'Curso')
            
            if not id_interno or pd.isna(id_interno): continue
            
            vista.log_curso_inicio(index + 1, len(df_input), id_curso_visible, nombre_curso)
            
            try:
                # NAVEGACIÓN DINÁMICA
                url_curso = f"https://upn.blackboard.com/ultra/courses/{id_interno}/outline"
                navegar_robusto(page, url_curso)
                
                # ... (resto de la lógica de carpetas e iframe se mantiene igual) ...
                boton = page.get_by_text("Sala videoconferencias | Class for Teams").first
                carpeta = page.get_by_text("MIS VIDEOCONFERENCIAS").first
                try: page.wait_for_selector("text=Contenido del curso", timeout=5000); 
                except: pass

                if not boton.is_visible() and carpeta.is_visible():
                    vista.log_accion("Abriendo carpeta...", icono="📂")
                    carpeta.click()
                    time.sleep(1)

                if boton.is_visible():
                    vista.log_accion("Entrando a Class...", icono="🖱️")
                    boton.click()
                    
                    frame_teams = None
                    intentos = 0
                    while intentos < 20:
                        for frame in page.frames:
                            try:
                                if frame.get_by_text("Próximamente").is_visible() or frame.get_by_text("Grabaciones").is_visible():
                                    frame_teams = frame
                                    break
                            except: pass
                        if frame_teams: break
                        time.sleep(1)
                        intentos += 1
                    
                    if frame_teams:
                        # Link Invitación
                        link_invitacion = "No encontrado"
                        try:
                            btn_inv = frame_teams.get_by_text("Copiar enlace de invitación")
                            if btn_inv.is_visible():
                                limpiar_portapapeles(page)
                                btn_inv.click()
                                time.sleep(0.5)
                                link_invitacion = leer_portapapeles(page)
                                vista.log_exito("Invitación capturada")
                        except: pass

                        # Grabaciones
                        tab_grab = frame_teams.get_by_text("Grabaciones")
                        if tab_grab.is_visible():
                            tab_grab.click()
                            time.sleep(3)
                            
                            filas = frame_teams.locator("tr")
                            count = filas.count()
                            
                            if count > 1:
                                vista.log_accion(f"Procesando {count-1} grabaciones...", icono="🎞️")
                                for i in range(1, count):
                                    row_locator = filas.nth(i)
                                    cols = row_locator.locator("td")
                                    
                                    fecha_raw = cols.nth(0).inner_text()
                                    duracion_txt = cols.nth(2).inner_text()
                                    link_grab = "No disponible"
                                    
                                    fecha_limpia, hora_ini, hora_fin = parsear_fecha_compleja(fecha_raw)
                                    
                                    celda_acciones = cols.last
                                    btn_menu = celda_acciones.locator("button").first 
                                    
                                    if "Grabando" in celda_acciones.inner_text():
                                        vista.log_alerta(f"En vivo (Omitido): {fecha_limpia}")
                                        link_grab = "EN_VIVO_GRABANDO"
                                    else:
                                        if btn_menu.is_visible():
                                            btn_menu.click()
                                            time.sleep(0.5)
                                            btn_copy = page.get_by_text("Copiar enlace", exact=True).first
                                            if not btn_copy.is_visible():
                                                btn_copy = frame_teams.get_by_text("Copiar enlace", exact=True).first
                                            
                                            if btn_copy.is_visible():
                                                limpiar_portapapeles(page)
                                                btn_copy.click()
                                                time.sleep(0.5)
                                                link_grab = leer_portapapeles(page)
                                                vista.log_exito(f"Video: {fecha_limpia} ({hora_ini}-{hora_fin})")
                                            
                                            page.keyboard.press("Escape")
                                            time.sleep(0.1)
                                            page.keyboard.press("Escape")
                                    
                                    all_recordings.append({
                                        "ID": id_curso_visible,
                                        "Curso": nombre_curso,
                                        "ID_Interno": id_interno,
                                        "Fecha": fecha_limpia,
                                        "Inicio": hora_ini,
                                        "Fin": hora_fin,
                                        "Duración": duracion_txt,
                                        "Link_Invitacion": link_invitacion,
                                        "Link_Grabacion": link_grab
                                    })
                            else:
                                vista.log_alerta("Carpeta de grabaciones vacía")
                        else:
                            vista.log_alerta("Pestaña Grabaciones no visible")
                    else:
                        vista.log_error("Timeout: Class no cargó iframe")
                else:
                    vista.log_error("Botón Class no encontrado")

            except Exception as e:
                vista.log_error(f"Error crítico en curso: {e}")
            
            vista.log_curso_fin()

        browser_context.close()

        if all_recordings:
            print(f"\n💾 Guardando reporte FINAL en: {OUTPUT_FILE}")
            df = pd.DataFrame(all_recordings)
            
            with pd.ExcelWriter(OUTPUT_FILE, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Reporte')
                ws = writer.sheets['Reporte']
                ws.set_column('A:A', 15)
                ws.set_column('D:F', 12) 
                ws.set_column('H:I', 60)
            print("✨ ¡FIN DEL PROCESO RPA!")

if __name__ == "__main__":
    run()