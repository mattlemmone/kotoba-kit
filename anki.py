import json
import os
import urllib.request
import base64
import requests
import logging
from typing import Dict, List, Optional, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Anki configuration
DEFAULT_DECK_NAME = "Japanese::Sentences"
DEFAULT_MODEL_NAME = "Basic"

# OpenAI configuration
OPENAI_MODEL = "gpt-3.5-turbo"
OPENAI_SYSTEM_PROMPT = "You are a translator. Translate the following Japanese text to English. Respond with only the translation."
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Error messages
ERR_NO_API_KEY = "OPENAI_API_KEY environment variable not found"
ERR_UNKNOWN = "unknown error: response missing result field"
ERR_FILE_NOT_FOUND = "Error: File '{}' does not exist"
ERR_NOT_MP3 = "Error: File must be an MP3"


def build_anki_connect_action(action: str, **params) -> Dict[str, Any]:
    """Build an AnkiConnect API request.
    
    Args:
        action: The AnkiConnect action to perform
        **params: Parameters for the action
        
    Returns:
        Dictionary containing the action request
    """
    return {'action': action, 'params': params, 'version': 6}


def invoke_anki_connect(action: str, **params) -> Any:
    """Execute an AnkiConnect API call.
    
    Args:
        action: The AnkiConnect action to perform
        **params: Parameters for the action
        
    Returns:
        The result of the AnkiConnect API call
        
    Raises:
        Exception: If the API call fails
    """
    request_json = json.dumps(build_anki_connect_action(action, **params)).encode('utf-8')
    response = json.load(urllib.request.urlopen(urllib.request.Request(
        'http://127.0.0.1:8765', request_json)))
    
    if 'result' not in response:
        if 'error' in response and response['error'] is not None:
            raise Exception(response['error'])
        raise Exception(ERR_UNKNOWN)
    
    return response['result']


def get_translation(text: str) -> str:
    """Get translation from OpenAI API.
    
    Args:
        text: The Japanese text to translate
        
    Returns:
        The English translation
        
    Raises:
        Exception: If the API call fails or the API key is not set
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise Exception(ERR_NO_API_KEY)

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': OPENAI_MODEL,
        'messages': [
            {
                'role': 'system',
                'content': OPENAI_SYSTEM_PROMPT
            },
            {
                'role': 'user',
                'content': text
            }
        ],
        'temperature': 0.3
    }
    
    response = requests.post(
        OPENAI_API_URL,
        headers=headers,
        json=payload
    )
    
    if response.status_code != 200:
        raise Exception(f'OpenAI API error: {response.text}')
    
    return response.json()['choices'][0]['message']['content'].strip()


def add_sentence_card(audio_path: str, deck_name: str = DEFAULT_DECK_NAME, 
                     model_name: str = DEFAULT_MODEL_NAME, 
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
    # Validate the audio file
    if not os.path.exists(audio_path):
        raise Exception(ERR_FILE_NOT_FOUND.format(audio_path))
    
    if not audio_path.lower().endswith('.mp3'):
        raise Exception(ERR_NOT_MP3)
    
    # Get the filename without extension as the front field
    filename = os.path.basename(audio_path)
    front_text = os.path.splitext(filename)[0]
    logger.info(f"Front text: {front_text}")
    
    # Get translation from OpenAI if no custom translation provided
    if custom_translation is not None:
        back_text = custom_translation
        logger.info(f"Using custom translation: {back_text}")
    else:
        logger.info("Getting translation from OpenAI...")
        back_text = get_translation(front_text)
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
    result = invoke_anki_connect('addNote', note=note)
    return result


def process_audio_files(audio_paths: List[str], deck_name: str = DEFAULT_DECK_NAME, 
                       model_name: str = DEFAULT_MODEL_NAME,
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
            note_id = add_sentence_card(
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