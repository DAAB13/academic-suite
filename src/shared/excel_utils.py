import shutil
import os
import pandas as pd


def copiar_archivo_onedrive(ruta_origen, ruta_destino):
    """
    Copia el archivo de OneDrive a la carpeta local.
    Si el archivo está abierto, devuelve la ruta original como fallback.
    """
    if os.path.exists(ruta_origen):
        try:
            # Intentamos la copia segura
            shutil.copy2(ruta_origen, ruta_destino)
            print(f"✨ Archivo sincronizado localmente en: {ruta_destino}")
            return ruta_destino
        except PermissionError:
            # Si alguien lo tiene abierto (o tú mismo), usamos el original
            print("⚠️ Archivo en uso. Se leerá directamente de OneDrive (puede haber retrasos de red).")
            return ruta_origen
    else:
        print(f"❌ ERROR CRÍTICO: No se encontró el archivo original en:\n{ruta_origen}")
        return None
    

def exportar_reporte_supervision(df_operativo, df_resumen, ruta_salida):
    """
    Genera el Excel de Supervisión con formato profesional (Tablas y filtros).
    """
    try:
        print(f"   🎨 Aplicando formato y guardando en: {ruta_salida}...")
        
        with pd.ExcelWriter(ruta_salida, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
            # 1. Guardar las hojas
            df_operativo.to_excel(writer, sheet_name='operativo', index=False)
            df_resumen.to_excel(writer, sheet_name='resumen', index=False)

            workbook = writer.book
            ws_operativa = writer.sheets['operativo']
            ws_resumen = writer.sheets['resumen']

            # 2. Definir Formatos
            f_center = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
            f_text = workbook.add_format({'num_format': '@', 'align': 'center', 'valign': 'vcenter'})

            # 3. Formato Hoja OPERATIVO
            (max_f, max_c) = df_operativo.shape
            if max_f > 0: # Solo si hay datos
                ws_operativa.add_table(0, 0, max_f, max_c - 1, {
                    'columns': [{'header': c} for c in df_operativo.columns],
                    'style': 'TableStyleMedium2',
                    'name': 'TablaOperativa'
                })
            ws_operativa.set_column(0, max_c - 1, 15, f_center) # Ancho general
            ws_operativa.set_column('F:F', 18, f_text)          # Sesión
            ws_operativa.set_column('B:C', 30)                  # Curso/Docente

            # 4. Formato Hoja RESUMEN
            (max_fr, max_cr) = df_resumen.shape
            if max_fr > 0:
                ws_resumen.add_table(0, 0, max_fr, max_cr - 1, {
                    'columns': [{'header': c} for c in df_resumen.columns],
                    'style': 'TableStyleMedium2',
                    'name': 'TablaResumen'
                })
            ws_resumen.set_column(0, max_cr - 1, 15, f_center)
            ws_resumen.set_column('B:C', 30)

        print("✨ Reporte creado correctamente.")
        return True
    except Exception as e:
        print(f"❌ Error al generar Excel: {e}")
        return False