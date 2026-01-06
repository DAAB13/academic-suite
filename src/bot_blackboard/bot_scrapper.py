import os
import pandas as pd
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
from src.bot_blackboard import vista_bot as vista #rich

def run():
    # ==========================================
    # CONFIGURACIÓN (Ajustada a 3 niveles)
    # ==========================================
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    INPUT_FILE = os.path.join(BASE_DIR, "01_data", "resumen_con_llave.xlsx")
    OUTPUT_DIR = os.path.join(BASE_DIR, "02_outputs", "bot_blackboard")
    OUTPUT_FILE = os.path.join(OUTPUT_DIR, "reporte_grabaciones.xlsx")
    USER_DATA_DIR = os.path.join(BASE_DIR, "00_inputs", "chrome_profile")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(USER_DATA_DIR), exist_ok=True)

    # Mapeo de meses
    MESES_EN = {
        "January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06",
        "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12"
    }

    # --- FUNCIONES HELPER (Mantienen tu lógica original) ---
    def parsear_fecha_compleja(texto_raw):
        fecha_fmt, inicio_fmt, fin_fmt = texto_raw, "", ""
        texto_limpio = texto_raw.replace("\n", " ").replace("\r", " ").strip()
        try:
            # Fecha
            match_fecha = re.search(r'([A-Za-z]+)\s+(\d+)(?:st|nd|rd|th)?,\s+(\d{4})', texto_limpio)
            if match_fecha:
                mes_txt, dia, anio = match_fecha.groups()
                mes_num = MESES_EN.get(mes_txt, "01")
                fecha_fmt = f"{int(dia):02d}/{mes_num}/{anio}"
            
            # Horas (Imán Agresivo)
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
    # LÓGICA PRINCIPAL (Ya no está indentada dentro de otro run)
    # ==========================================
    if not os.path.exists(INPUT_FILE):
        print("❌ Error: Falta resumen_con_llave.xlsx")
        return

    df_input = pd.read_excel(INPUT_FILE, dtype={'ID': str})
    all_recordings = []

    # [VISUAL] Tabla de Pre-vuelo en lugar de print simple
    vista.mostrar_tabla_prevuelo(df_input)

    with sync_playwright() as p:
        try:
            browser_context = p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                channel="chrome", 
                args=["--start-maximized", "--disable-web-security"],
                permissions=["clipboard-read", "clipboard-write"]
            )
        except Exception as e:
            print(f"❌ Error lanzando Chrome: {e}")
            return

        page = browser_context.pages[0]

        print("\n🔑 PASO 1: LOGIN MANUAL")
        page.goto("https://upn-colaborador.blackboard.com/")
        input("👉 LOGUEATE, ESPERA A VER TUS CURSOS Y PRESIONA ENTER... ")
        print("⏳ Enfriando (3s)...")
        time.sleep(3)

        for index, row in df_input.iterrows():
            id_curso_visible = row.get('ID', 'SinID')
            id_interno = row.get('ID_Interno')
            nombre_curso = row.get('CURSO', 'Curso')
            
            if not id_interno or pd.isna(id_interno): continue
            
            # [VISUAL] Inicio de tarjeta de curso
            vista.log_curso_inicio(index + 1, len(df_input), id_curso_visible, nombre_curso)
            
            try:
                # 1. NAVEGACIÓN
                url_curso = f"https://upn.blackboard.com/ultra/courses/{id_interno}/outline"
                navegar_robusto(page, url_curso)
                
                # 2. CARPETAS
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
                    
                    # 3. ESPERAR IFRAME
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
                                    
                                    # Extracción
                                    fecha_raw = cols.nth(0).inner_text()
                                    duracion_txt = cols.nth(2).inner_text()
                                    link_grab = "No disponible"
                                    
                                    # Parseo
                                    fecha_limpia, hora_ini, hora_fin = parsear_fecha_compleja(fecha_raw)
                                    
                                    # Link Video
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
            
            # [VISUAL] Cierre de tarjeta
            vista.log_curso_fin()

        browser_context.close()

        if all_recordings:
            print(f"\n💾 Guardando reporte FINAL en: {OUTPUT_FILE}")
            df = pd.DataFrame(all_recordings)
            with pd.ExcelWriter(OUTPUT_FILE, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Reporte')
                ws = writer.sheets['Reporte']
                ws.set_column('A:A', 15)
                ws.set_column('D:F', 12) # Fecha y Horas
                ws.set_column('H:I', 60)
            print("✨ ¡FIN!")

if __name__ == "__main__":
    run()