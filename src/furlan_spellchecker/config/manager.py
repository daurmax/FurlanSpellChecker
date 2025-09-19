"""Simple config manager for FurlanSpellChecker.

Stores a JSON file in the platform-appropriate user config directory.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


def _default_config_path() -> Path:
    """Return default user config file path."""
    if "LOCALAPPDATA" in __import__("os").environ:
        base = Path(__import__("os").environ["LOCALAPPDATA"])
    else:
        base = Path.home() / ".config"
    cfg_dir = base / "furlan_spellchecker"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir / "config.json"


class ConfigManager:
    """Very small config manager.

    API:
    - load() -> Dict
    - save(dict)
    """

    @staticmethod
    def load(path: Optional[str] = None) -> Dict[str, Any]:
        p = Path(path) if path else _default_config_path()
        if not p.exists():
            return {}
        try:
            with p.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}

    @staticmethod
    def save(data: Dict[str, Any], path: Optional[str] = None) -> None:
        p = Path(path) if path else _default_config_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
