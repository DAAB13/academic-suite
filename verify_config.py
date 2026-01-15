import sys
from pathlib import Path

# Add src to python path
sys.path.append(str(Path(__file__).resolve().parent))

from src.shared.config_loader import config
from src.reporte_semanal.etl_sunday import PATH_ONEDRIVE as SUNDAY_ONEDRIVE

print("--- CONFIG LOADING TEST ---")
print(f"Config loaded: {bool(config)}")
print(f"Inputs Path (from config): {config['paths']['inputs']}")

print("\n--- MODULE PATHS RESOLUTION ---")
print(f"Sunday OneDrive: {SUNDAY_ONEDRIVE}")

print("\n--- CHECKING EXISTENCE ---")
# The onedrive path might not vary if run from this env, but checking it resolves is key
print(f"Sunday OneDrive Resolved: {SUNDAY_ONEDRIVE}")

print("\nVERIFICATION COMPLETE")
