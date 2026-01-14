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
            "model": "gpt-4o",
            "system_prompt": "You are a translator. Translate the following Japanese text to English. Respond with only the translation."
        },
        "paths": {
            "output_dir": None  # Default to current directory
        }
    }
    
    def __init__(self):
        """Initialize configuration with hardcoded defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
    
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
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current 