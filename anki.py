import json
import os
import urllib.request
import base64
import logging
from typing import Dict, List, Optional, Tuple, Any
from translator import Translator

# Configure logging
logger = logging.getLogger(__name__)

class AnkiConnector:
    """Interface with Anki Connect API."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Anki connector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.host = self.config.get("host", "127.0.0.1")
        self.port = self.config.get("port", 8765)
        self.default_deck = self.config.get("default_deck", "Japanese::Sentences")
        self.default_model = self.config.get("default_model", "Basic")
        
        # Create translator instance
        translator_config = self.config.get("translator", {})
        self.translator = Translator(translator_config)
    
    def build_action(self, action: str, **params) -> Dict[str, Any]:
        """Build an AnkiConnect API request.
        
        Args:
            action: The AnkiConnect action to perform
            **params: Parameters for the action
            
        Returns:
            Dictionary containing the action request
        """
        return {'action': action, 'params': params, 'version': 6}
    
    def invoke(self, action: str, **params) -> Any:
        """Execute an AnkiConnect API call.
        
        Args:
            action: The AnkiConnect action to perform
            **params: Parameters for the action
            
        Returns:
            The result of the AnkiConnect API call
            
        Raises:
            Exception: If the API call fails
        """
        request_json = json.dumps(self.build_action(action, **params)).encode('utf-8')
        url = f'http://{self.host}:{self.port}'
        
        response = json.load(urllib.request.urlopen(urllib.request.Request(url, request_json)))
        
        if 'result' not in response:
            if 'error' in response and response['error'] is not None:
                raise Exception(response['error'])
            raise Exception("unknown error: response missing result field")
        
        return response['result']
    
    def add_sentence_card(self, audio_path: str, deck_name: Optional[str] = None, 
                         model_name: Optional[str] = None, 
                         custom_translation: Optional[str] = None) -> int:
        """Add a new sentence card to Anki.
        
        Args:
            audio_path: Path to the MP3 file
            deck_name: Name of the Anki deck to add the card to
            model_name: Name of the Anki note model to use
            custom_translation: Optional custom translation to use instead of API translation
            
        Returns:
            The ID of the newly created note
            
        Raises:
            Exception: If the file doesn't exist or isn't an MP3
        """
        # Use default values if not provided
        deck_name = deck_name or self.default_deck
        model_name = model_name or self.default_model
        
        # Validate the audio file
        if not os.path.exists(audio_path):
            raise Exception(f"Error: File '{audio_path}' does not exist")
        
        if not audio_path.lower().endswith('.mp3'):
            raise Exception("Error: File must be an MP3")
        
        # Get the filename without extension as the front field
        filename = os.path.basename(audio_path)
        front_text = os.path.splitext(filename)[0]
        logger.info(f"Front text: {front_text}")
        
        # Get translation if no custom translation provided
        if custom_translation is not None:
            back_text = custom_translation
            logger.info(f"Using custom translation: {back_text}")
        else:
            logger.info("Getting translation...")
            back_text = self.translator.translate(front_text)
            logger.info(f"Translation: {back_text}")
        
        # Read the audio file as base64
        logger.info("Processing audio data...")
        with open(audio_path, 'rb') as audio_file:
            audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
        
        # Create the note
        logger.info("Adding note to Anki...")
        note = {
            "deckName": deck_name,
            "modelName": model_name,
            "fields": {
                "Front": front_text,
                "Back": back_text
            },
            "tags": ["script_added"],
            "audio": [{
                "data": audio_data,
                "filename": filename,
                "fields": ["Audio"]
            }]
        }
        
        # Add the note to Anki
        result = self.invoke('addNote', note=note)
        return result
    
    def process_audio_files(self, audio_paths: List[str], deck_name: Optional[str] = None, 
                           model_name: Optional[str] = None,
                           custom_translation: Optional[str] = None) -> Tuple[List[str], List[Tuple[str, str]]]:
        """Process multiple audio files and add them to Anki.
        
        Args:
            audio_paths: List of paths to MP3 files
            deck_name: Name of the Anki deck to add the cards to
            model_name: Name of the Anki note model to use
            custom_translation: Optional custom translation to use instead of API translation
            
        Returns:
            Tuple containing (successful_files, failed_files)
        """
        successful_files = []
        failed_files = []  # List of (file, error) tuples
        
        for audio_path in audio_paths:
            logger.info(f"Processing file: {audio_path}")
            
            try:
                note_id = self.add_sentence_card(
                    audio_path, 
                    deck_name=deck_name, 
                    model_name=model_name,
                    custom_translation=custom_translation
                )
                logger.info(f"Success! Added note with ID: {note_id}")
                successful_files.append(audio_path)
            except Exception as e:
                logger.error(f"Failed to add card for {audio_path}: {str(e)}")
                failed_files.append((audio_path, str(e)))
        
        return successful_files, failed_files 