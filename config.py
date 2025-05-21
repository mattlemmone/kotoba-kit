import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Configuration manager for KotobaKit."""
    
    DEFAULT_CONFIG = {
        "tts": {
            "url": "https://ondoku3.com/ja/text_to_speech/",
            "voice": "ja-JP-Wavenet-C",
            "speed": 1,
            "pitch": 0
        },
        "anki": {
            "host": "127.0.0.1",
            "port": 8765,
            "default_deck": "Japanese::Sentences",
            "default_model": "Basic"
        },
        "openai": {
            "model": "gpt-4o-mini",
            "system_prompt": "You are a translator. Translate the following Japanese text to English. Respond with only the translation."
        },
        "paths": {
            "output_dir": None  # Default to current directory
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to config file, defaults to ~/.kotobakit/config.json
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path.home() / ".kotobakit" / "config.json"
            
        self.config = self.DEFAULT_CONFIG.copy()
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file if it exists."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    self._update_nested_dict(self.config, user_config)
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def _update_nested_dict(self, d: Dict[str, Any], u: Dict[str, Any]) -> None:
        """Update nested dictionary recursively."""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
    
    def save(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            *keys: Sequence of keys to navigate nested dictionaries
            default: Default value if key doesn't exist
            
        Returns:
            The configuration value or default
        """
        current = self.config
        for key in keys:
            if key not in current:
                return default
            current = current[key]
        return current 