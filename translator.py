import os
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class Translator:
    """Handles translation of Japanese text to English."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the translator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.model = self.config.get("model", "gpt-3.5-turbo")
        self.system_prompt = self.config.get(
            "system_prompt", 
            "You are a translator. Translate the following Japanese text to English. Respond with only the translation."
        )
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def translate(self, text: str) -> str:
        """Translate Japanese text to English using OpenAI API.
        
        Args:
            text: The Japanese text to translate
            
        Returns:
            The English translation
            
        Raises:
            Exception: If the API call fails or the API key is not set
        """
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise Exception("OPENAI_API_KEY environment variable not found")

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': self.system_prompt
                },
                {
                    'role': 'user',
                    'content': text
                }
            ],
            'temperature': 0.3
        }
        
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f'OpenAI API error: {response.text}')
        
        return response.json()['choices'][0]['message']['content'].strip()


# For backward compatibility
def translate(text: str) -> str:
    """Legacy function for backward compatibility."""
    translator = Translator()
    return translator.translate(text) 