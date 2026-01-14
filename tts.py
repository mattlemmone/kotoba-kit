import os
import requests
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class TTSEngine:
    """Text-to-speech engine for Japanese."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the TTS engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.url = self.config.get("url", "https://ondoku3.com/ja/text_to_speech/")
        self.voice = self.config.get("voice", "ja-JP-Wavenet-C")
        self.speed = self.config.get("speed", 1)
        self.pitch = self.config.get("pitch", 0)
        self.boundary = "----WebKitFormBoundaryqGStFWB7U9DoxCXA"
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": f"multipart/form-data; boundary={self.boundary}",
            "priority": "u=1, i",
            "sec-ch-ua": '"Not?A_Brand";v="99", "Chromium";v="130"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-csrftoken": "efSzSFCU3ccRxThj1CeqUUNz1TDrhJ7Ysm0cJJtfFVOOreB8mTg0pGjBqS2TUovT",
            "x-requested-with": "XMLHttpRequest",
            "cookie": f'settings={{"voice":"{self.voice}","speed":{self.speed},"pitch":{self.pitch},"language":"ja-JP"}}; csrftoken=ohiN1e1vMTM74vuZvrcKFWGcz9zCNPy5',
            "Referer": "https://ondoku3.com/ja/",
            "Referrer-Policy": "same-origin",
        }
    
    def create_request_body(self, text: str) -> str:
        """Create the multipart form data request body for the TTS API.
        
        Args:
            text: The Japanese text to convert to speech
            
        Returns:
            A properly formatted multipart form data string
        """
        return (
            f"--{self.boundary}\r\n"
            f"Content-Disposition: form-data; name=\"text\"\r\n\r\n"
            f"{text}\r\n"
            f"--{self.boundary}\r\n"
            f"Content-Disposition: form-data; name=\"voice\"\r\n\r\n"
            f"{self.voice}\r\n"
            f"--{self.boundary}\r\n"
            f"Content-Disposition: form-data; name=\"speed\"\r\n\r\n"
            f"{self.speed}\r\n"
            f"--{self.boundary}\r\n"
            f"Content-Disposition: form-data; name=\"pitch\"\r\n\r\n"
            f"{self.pitch}\r\n"
            f"--{self.boundary}--\r\n"
        )
    
    def fetch_text_to_speech(self, text: str) -> Dict[str, str]:
        """Fetch TTS data for a given text.

        Args:
            text: The Japanese text to convert to speech

        Returns:
            Dictionary with URL and text

        Raises:
            Exception: If the API request fails
        """
        body = self.create_request_body(text)
        try:
            response = requests.post(self.url, headers=self.headers, data=body)

            if response.status_code == 200:
                result = response.json()
                return {"url": result["url"], "text": text}
            else:
                raise Exception(f"TTS API returned status {response.status_code} for text: \"{text}\"")
        except requests.RequestException as e:
            raise Exception(f"Error fetching text to speech for \"{text}\": {str(e)}")
    
    def download_file(self, url: str, download_path: str) -> None:
        """Download a file from a URL to a local path.

        Args:
            url: The URL to download from
            download_path: The local path to save the file to

        Raises:
            Exception: If the download fails
        """
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(download_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
        except Exception as e:
            # Delete the file if it exists and there was an error
            if os.path.exists(download_path):
                os.unlink(download_path)
            raise Exception(f"Download failed for {download_path}: {str(e)}")
    
    def generate_audio(self, phrases: List[str], output_dir: Optional[str] = None) -> List[str]:
        """Generate audio files for the given Japanese phrases.

        Args:
            phrases: List of Japanese phrases to convert to speech
            output_dir: Optional directory to save files to

        Returns:
            List of paths to the downloaded MP3 files

        Raises:
            Exception: If no audio files could be generated
        """
        if not phrases:
            raise Exception("No phrases provided for audio generation")

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
            result = self.fetch_text_to_speech(phrase)
            results.append(result)

        # Download each audio file
        for result in results:
            filename = f"{result['text']}.mp3"
            file_path = os.path.join(output_dir, filename)
            logger.info(f"Downloading: {filename}")

            self.download_file(result['url'], file_path)
            downloaded_files.append(file_path)

        if not downloaded_files:
            raise Exception("Failed to generate any audio files")

        return downloaded_files 