import yaml
from pathlib import Path

# Build paths relative to the project root
# Assuming this file is in src/shared/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"

def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# Global accessibility
config = load_config()
