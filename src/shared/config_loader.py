import yaml
from pathlib import Path

#------------------------
# NAVEGACIÓN DE CARPETAS
#------------------------

# BASE_DIR es la brújula del proyecto
# Path(__file__) toma la ubicación de este archivo
# resolve() sube tres niveles de carpetas para llegar a la raíz del proyecto.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

CONFIG_PATH = BASE_DIR / "config.yaml"

def load_config():
    """Busca y lee el archivo config.yaml para que Python entienda las rutas."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")
    # abrimos yaml
    with open(CONFIG_PATH, "r", encoding="utf-8") as f: # abrimos yaml
        return yaml.safe_load(f) # # yaml.safe_load convierte el texto del YAML en un Diccionario de Python

# Al importar este archivo en otros lados, ya tendrás acceso a toda tu configuración.
config = load_config()
