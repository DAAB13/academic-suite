import shutil
import pandas as pd
from pathlib import Path
# Importamos la configuración para tenerla disponible si fuera necesaria
from src.shared.config_loader import config, BASE_DIR

def copiar_archivo_onedrive(ruta_origen, ruta_destino):
    """
    Copia el archivo de OneDrive a la carpeta local de forma segura.
    Si el archivo está abierto, devuelve la ruta original como fallback.
    """
    # Convertimos a objetos Path para asegurar que funcionen en cualquier sistema
    path_origen = Path(ruta_origen)
    path_destino = Path(ruta_destino)

    if path_origen.exists():
        try:
            # Creamos la carpeta de destino si no existe
            path_destino.parent.mkdir(parents=True, exist_ok=True)
            
            # shutil.copy2 copia el archivo y mantiene la fecha original de modificación
            shutil.copy2(path_origen, path_destino)
            print(f"✨ Archivo sincronizado localmente en: {path_destino.name}")
            return str(path_destino)
            
        except PermissionError:
            # Este error ocurre si tú o Wilbert tienen el Excel abierto en ese momento
            print("⚠️ Archivo en uso. Se leerá directamente de OneDrive (puede haber retrasos de red).")
            return str(path_origen)
        except Exception as e:
            print(f"❌ Error inesperado al copiar: {e}")
            return str(path_origen)
    else:
        print(f"❌ ERROR CRÍTICO: No se encontró el archivo original en:\n{path_origen}")
        return None
    

def exportar_reporte_supervision(df_operativo, df_resumen, ruta_salida):
    """
    Genera el Excel de Supervisión con formato profesional (Tablas, filtros y anchos de columna).
    """
    try:
        path_salida = Path(ruta_salida)
        print(f"   🎨 Aplicando formato y guardando en: {path_salida.name}...")
        
        # Usamos ExcelWriter con el motor 'xlsxwriter' que permite dar formato a las celdas
        with pd.ExcelWriter(path_salida, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            
            # 1. GUARDAR LAS HOJAS
            # Escribimos los datos de Pandas a las hojas correspondientes
            df_operativo.to_excel(writer, sheet_name='operativo', index=False)
            df_resumen.to_excel(writer, sheet_name='resumen', index=False)

            # Accedemos al motor de escritura para personalizar el diseño
            workbook = writer.book
            ws_operativa = writer.sheets['operativo']
            ws_resumen = writer.sheets['resumen']

            # 2. DEFINIR FORMATOS ESTÉTICOS
            # Alineación centrada para que se vea ordenado
            f_center = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
            # Formato de texto para columnas que no deben cambiar (como IDs o Sesiones)
            f_text = workbook.add_format({'num_format': '@', 'align': 'center', 'valign': 'vcenter'})

            # 3. FORMATO HOJA 'OPERATIVO'
            # Obtenemos el tamaño de la tabla (filas y columnas)
            (max_f, max_c) = df_operativo.shape
            if max_f > 0: # Solo aplicamos formato si hay datos
                # Convertimos el rango de celdas en una "Tabla de Excel" oficial con filtros
                ws_operativa.add_table(0, 0, max_f, max_c - 1, {
                    'columns': [{'header': c} for c in df_operativo.columns],
                    'style': 'TableStyleMedium2', # Un estilo azul profesional
                    'name': 'TablaOperativa'
                })
            
            # Ajustamos los anchos de columna para que el texto no se vea cortado
            ws_operativa.set_column(0, max_c - 1, 15, f_center) # Ancho estándar
            ws_operativa.set_column('F:F', 18, f_text)          # Columna de Sesión un poco más ancha
            ws_operativa.set_column('B:C', 35)                 # Columnas de Curso y Docente (más largas)

            # 4. FORMATO HOJA 'RESUMEN'
            (max_fr, max_cr) = df_resumen.shape
            if max_fr > 0:
                ws_resumen.add_table(0, 0, max_fr, max_cr - 1, {
                    'columns': [{'header': c} for c in df_resumen.columns],
                    'style': 'TableStyleMedium2',
                    'name': 'TablaResumen'
                })
            
            ws_resumen.set_column(0, max_cr - 1, 15, f_center)
            ws_resumen.set_column('B:C', 35)

        print("✨ Reporte creado correctamente.")
        return True
    except Exception as e:
        print(f"❌ Error al generar Excel: {e}")
        return False