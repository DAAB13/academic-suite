import pandas as pd
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from src.shared.config_loader import config, BASE_DIR

console = Console()

def auditar_anomalias(df_diego):
    """
    Recibe el DataFrame completo de DIEGO (pasado + futuro) y busca errores.
    """
    print("\n--- 🚨 AUDITORÍA DE DATOS (ALERTAS) ---")
    
    lista_alertas = []
    
    # Configuración de Rutas para validar el Mapa
    # FILE_MAPA_IDS apunta al CSV en 01_data/bot_blackboard/
    FILE_MAPA_IDS = BASE_DIR / config['paths']['data'] / config['files']['base_maestra_ids']
    
    # ARCHIVO_ALERTAS ahora será un CSV en 01_data/operaciones/
    ARCHIVO_ALERTAS = BASE_DIR / config['paths']['data'] / config['files']['reporte_alertas']
    
    # Aseguramos que la carpeta 01_data/operaciones exista
    ARCHIVO_ALERTAS.parent.mkdir(parents=True, exist_ok=True)
    
    hoy = pd.Timestamp.now().normalize()

    # ==============================================================================
    # 1. ALERTA CRÍTICA: ID FALTANTE EN MAPA (Actualizado a CSV)
    # ==============================================================================
    ids_en_excel = set(df_diego[df_diego['ESTADO DE CLASE'].isna()]['ID'].unique()) # Solo nos preocupan los pendientes
    
    if os.path.exists(FILE_MAPA_IDS):
        # Leemos el CSV con la configuración correcta (separador ; y latin1)
        df_mapa = pd.read_csv(FILE_MAPA_IDS, sep=';', dtype={'ID': str}, encoding='latin1')
        ids_en_mapa = set(df_mapa['ID'].unique())
        
        # ¿Qué IDs tengo en mi Excel que NO están en el Mapa?
        ids_sin_mapa = ids_en_excel - ids_en_mapa
        
        for id_missing in ids_sin_mapa:
            lista_alertas.append({
                'ID': id_missing, 
                'Tipo': 'CRÍTICO: Falta en Mapa', 
                'Detalle': 'El Bot fallará. Ejecuta "actualizar-mapa"', 
                'Acción': 'Correr script mapa'
            })
    else:
        console.print(f"[bold red]❌ No se encontró {FILE_MAPA_IDS}. Imposible validar mapa.[/bold red]")

    # ==============================================================================
    # 2. ALERTA: CLASES EN EL LIMBO (Pasado sin estado)
    # ==============================================================================
    # Buscamos fechas menores a hoy que NO tengan estado (están vacías)
    df_limbo = df_diego[(df_diego['FECHAS'] < hoy) & (df_diego['ESTADO DE CLASE'].isna())]
    
    for _, row in df_limbo.iterrows():
        lista_alertas.append({
            'ID': row['ID'],
            'Tipo': 'Gestión: Clase en Limbo',
            'Detalle': f"Fecha {row['FECHAS'].strftime('%d/%m')} sin Estado",
            'Acción': 'Actualizar Excel Panel'
        })

    # ==============================================================================
    # 3. ALERTA: DATOS FALTANTES (Futuro incompleto)
    # ==============================================================================
    # Buscamos clases futuras que les falte sesión o docente
    df_futuro = df_diego[df_diego['FECHAS'] >= hoy]
    df_incompleto = df_futuro[df_futuro['SESIÓN'].isna() | df_futuro['DOCENTE'].isna()]
    
    for _, row in df_incompleto.iterrows():
        lista_alertas.append({
            'ID': row['ID'],
            'Tipo': 'Datos Faltantes',
            'Detalle': f"Falta Docente o Sesión para {row['FECHAS'].strftime('%d/%m')}",
            'Acción': 'Completar datos'
        })

    # ==============================================================================
    # 4. ALERTAS DE CONSISTENCIA
    # ==============================================================================
    for id_val, grupo in df_diego.groupby('ID'):
        # Nombre Contradictorio
        c_unicos = grupo['CURSO'].dropna().unique()
        if len(c_unicos) > 1:
            lista_alertas.append({
                'ID': id_val, 
                'Tipo': 'Nombre Contradictorio', 
                'Detalle': " / ".join(str(x) for x in c_unicos), 
                'Acción': 'Unificar nombre'
            })
        
        # Múltiples Docentes
        d_unicos = grupo['DOCENTE'].dropna().unique()
        if len(d_unicos) > 1:
            lista_alertas.append({
                'ID': id_val, 
                'Tipo': 'Múltiples Docentes', 
                'Detalle': " / ".join(str(x) for x in d_unicos), 
                'Acción': 'Verificar reemplazo'
            })

    # ==============================================================================
    # 5. RESULTADOS (Exportación a CSV)
    # ==============================================================================
    if lista_alertas:
        df_alertas = pd.DataFrame(lista_alertas)
        
        # A. Mostrar en Terminal (Rich Table) - ¡Vistazo Rápido!
        table = Table(title="🚨 ALERTAS DETECTADAS", style="red")
        table.add_column("ID", style="cyan")
        table.add_column("Tipo", style="bold red")
        table.add_column("Detalle", style="white")
        
        for alerta in lista_alertas:
            table.add_row(str(alerta['ID']), alerta['Tipo'], str(alerta['Detalle']))
        
        console.print(table)
        
        # B. Guardar CSV (Ligero y Rápido) en 01_data/operaciones/
        try:
            # Usamos ; y latin1 para compatibilidad total con Excel en español
            df_alertas.to_csv(ARCHIVO_ALERTAS, index=False, sep=';', encoding='latin1')
            
            console.print(f"[yellow]📂 Reporte detallado guardado en: {ARCHIVO_ALERTAS}[/yellow]")
            return True
            
        except Exception as e:
            console.print(f"[bold red]❌ Error al guardar alertas: {e}[/bold red]")
            return False
            
    else:
        console.print("[bold green]✨ ¡Todo limpio! No se detectaron anomalías operativas.[/bold green]")
        return False