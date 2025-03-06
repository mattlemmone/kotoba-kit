import os
import requests
import logging
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BOUNDARY = "----WebKitFormBoundaryqGStFWB7U9DoxCXA"
URL = "https://ondoku3.com/ja/text_to_speech/"
HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": f"multipart/form-data; boundary={BOUNDARY}",
    "priority": "u=1, i",
    "sec-ch-ua": '"Not?A_Brand";v="99", "Chromium";v="130"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-csrftoken": "efSzSFCU3ccRxThj1CeqUUNz1TDrhJ7Ysm0cJJtfFVOOreB8mTg0pGjBqS2TUovT",
    "x-requested-with": "XMLHttpRequest",
    "cookie": 'settings={"voice":"ja-JP-Wavenet-C","speed":1,"pitch":0,"language":"ja-JP"}; csrftoken=ohiN1e1vMTM74vuZvrcKFWGcz9zCNPy5',
    "Referer": "https://ondoku3.com/ja/",
    "Referrer-Policy": "same-origin",
}


def create_request_body(text: str) -> str:
    """Create the multipart form data request body for the TTS API.
    
    Args:
        text: The Japanese text to convert to speech
        
    Returns:
        A properly formatted multipart form data string
    """
    return (
        f"--{BOUNDARY}\r\n"
        f"Content-Disposition: form-data; name=\"text\"\r\n\r\n"
        f"{text}\r\n"
        f"--{BOUNDARY}\r\n"
        f"Content-Disposition: form-data; name=\"voice\"\r\n\r\n"
        f"ja-JP-Wavenet-C\r\n"
        f"--{BOUNDARY}\r\n"
        f"Content-Disposition: form-data; name=\"speed\"\r\n\r\n"
        f"1\r\n"
        f"--{BOUNDARY}\r\n"
        f"Content-Disposition: form-data; name=\"pitch\"\r\n\r\n"
        f"0\r\n"
        f"--{BOUNDARY}--\r\n"
    )


def fetch_text_to_speech(url: str, text: str) -> Optional[Dict]:
    """Fetch TTS data for a given text.
    
    Args:
        url: The TTS API URL
        text: The Japanese text to convert to speech
        
    Returns:
        Dictionary with URL and text if successful, None otherwise
    """
    body = create_request_body(text)
    try:
        response = requests.post(url, headers=HEADERS, data=body)
        
        if response.status_code == 200:
            result = response.json()
            return {"url": result["url"], "text": text}
        else:
            logger.error(f"Failed to fetch for text: \"{text}\"")
            return None
    except Exception as e:
        logger.error(f"Error fetching text to speech for \"{text}\": {str(e)}")
        return None


def download_file(url: str, download_path: str) -> bool:
    """Download a file from a URL to a local path.
    
    Args:
        url: The URL to download from
        download_path: The local path to save the file to
        
    Returns:
        True if download was successful, False otherwise
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(download_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        return True
    except Exception as e:
        # Delete the file if it exists and there was an error
        if os.path.exists(download_path):
            os.unlink(download_path)
        logger.error(f"Download failed: {str(e)}")
        return False


def fetch_and_download(url: str, phrases: List[str], output_dir: str = None) -> List[str]:
    """Fetch TTS data for multiple phrases and download the resulting audio files.
    
    Args:
        url: The TTS API URL
        phrases: List of Japanese phrases to convert to speech
        output_dir: Optional directory to save files to (defaults to current directory)
        
    Returns:
        List of paths to the downloaded MP3 files
    """
    if not phrases:
        logger.warning("No phrases provided")
        return []
    
    # Set default output directory to current directory if not specified
    if output_dir is None:
        output_dir = os.getcwd()
    else:
        # Create the directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    # Fetch TTS data for each phrase
    results = []
    downloaded_files = []
    
    for phrase in phrases:
        result = fetch_text_to_speech(url, phrase)
        if result:
            results.append(result)
    
    # Download each audio file
    for result in results:
        filename = f"{result['text']}.mp3"
        file_path = os.path.join(output_dir, filename)
        logger.info(f"Downloading: {filename}")
        
        if download_file(result['url'], file_path):
            downloaded_files.append(file_path)
    
    return downloaded_files


def generate_audio(phrases: List[str], output_dir: str = None) -> List[str]:
    """Generate audio files for the given Japanese phrases.
    
    Args:
        phrases: List of Japanese phrases to convert to speech
        output_dir: Optional directory to save files to
        
    Returns:
        List of paths to the downloaded MP3 files
    """
    return fetch_and_download(URL, phrases, output_dir)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python tts.py <japanese_phrase> [<japanese_phrase> ...]")
        sys.exit(1)
    
    phrases = sys.argv[1:]
    downloaded_files = generate_audio(phrases)
    
    if downloaded_files:
        print(f"Successfully downloaded {len(downloaded_files)} audio files:")
        for file_path in downloaded_files:
            print(f"  - {file_path}")
    else:
        print("No audio files were downloaded.")
        sys.exit(1) 