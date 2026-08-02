import os
import json
from pathlib import Path

CONFIG_FILE = "config.json"

def load_config() -> dict:
    """Loads the user configuration or creates a default one if it doesn't exist."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        default_config = {
            "obsidian_path": os.path.abspath("mis_notas_obsidian"),
            "model_name": "qwen2.5:3b"
        }
        save_config(default_config)
        return default_config

def save_config(config: dict) -> None:
    """Saves the configuration to a local JSON file."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def update_obsidian_path(config: dict, new_path: str) -> bool:
    """Updates the Obsidian path in the config if the path is valid or can be created."""
    new_path = new_path.strip().replace('"', '').replace("'", "")
    if not new_path:
        return False
        
    path_obj = Path(new_path)
    if not path_obj.exists():
        try:
            path_obj.mkdir(parents=True, exist_ok=True)
        except Exception:
            return False
            
    config["obsidian_path"] = str(path_obj.absolute())
    save_config(config)
    return True

def update_model_name(config: dict, new_model: str) -> bool:
    """Updates the LLM model name in the config."""
    new_model = new_model.strip()
    if not new_model:
        return False
        
    config["model_name"] = new_model
    save_config(config)
    return True
