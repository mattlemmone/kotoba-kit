import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile

import tts


class TestTts(unittest.TestCase):
    
    def test_create_request_body(self):
        """Test that the request body is created correctly."""
        text = "こんにちは"
        body = tts.create_request_body(text)
        
        # Check that the text is in the body
        self.assertIn(text, body)
        # Check that the boundary is in the body
        self.assertIn(tts.BOUNDARY, body)
        # Check that the voice is in the body
        self.assertIn("ja-JP-Wavenet-C", body)
    
    @patch('tts.requests.post')
    def test_fetch_text_to_speech_success(self, mock_post):
        """Test successful TTS fetch."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"url": "https://example.com/audio.mp3"}
        mock_post.return_value = mock_response
        
        result = tts.fetch_text_to_speech(tts.URL, "こんにちは")
        
        # Check that the result is correct
        self.assertEqual(result["url"], "https://example.com/audio.mp3")
        self.assertEqual(result["text"], "こんにちは")
        
        # Check that the request was made with the correct parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], tts.URL)
        self.assertEqual(kwargs["headers"], tts.HEADERS)
    
    @patch('tts.requests.post')
    def test_fetch_text_to_speech_failure(self, mock_post):
        """Test failed TTS fetch."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        result = tts.fetch_text_to_speech(tts.URL, "こんにちは")
        
        # Check that the result is None
        self.assertIsNone(result)
    
    @patch('tts.requests.get')
    def test_download_file_success(self, mock_get):
        """Test successful file download."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"test data"]
        mock_get.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = tts.download_file("https://example.com/audio.mp3", temp_path)
            
            # Check that the result is True
            self.assertTrue(result)
            
            # Check that the file exists and has content
            self.assertTrue(os.path.exists(temp_path))
            with open(temp_path, 'rb') as f:
                content = f.read()
                self.assertEqual(content, b"test data")
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('tts.fetch_text_to_speech')
    @patch('tts.download_file')
    def test_fetch_and_download(self, mock_download, mock_fetch):
        """Test fetch and download process."""
        # Mock the fetch response
        mock_fetch.return_value = {"url": "https://example.com/audio.mp3", "text": "こんにちは"}
        
        # Mock the download response
        mock_download.return_value = True
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = tts.fetch_and_download(tts.URL, ["こんにちは"], temp_dir)
            
            # Check that the result contains the expected file path
            expected_path = os.path.join(temp_dir, "こんにちは.mp3")
            self.assertEqual(result, [expected_path])
            
            # Check that fetch_text_to_speech was called with the correct parameters
            mock_fetch.assert_called_once_with(tts.URL, "こんにちは")
            
            # Check that download_file was called with the correct parameters
            mock_download.assert_called_once_with("https://example.com/audio.mp3", expected_path)


if __name__ == '__main__':
    unittest.main() 