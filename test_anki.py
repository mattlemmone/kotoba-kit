import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
import json

import anki


class TestAnki(unittest.TestCase):
    
    def test_build_anki_connect_action(self):
        """Test that the AnkiConnect action is built correctly."""
        action = "addNote"
        params = {"note": {"deckName": "test", "modelName": "test"}}
        
        result = anki.build_anki_connect_action(action, **params)
        
        # Check that the result has the correct structure
        self.assertEqual(result["action"], action)
        self.assertEqual(result["params"], params)
        self.assertEqual(result["version"], 6)
    
    @patch('anki.urllib.request.urlopen')
    @patch('anki.urllib.request.Request')
    def test_invoke_anki_connect_success(self, mock_request, mock_urlopen):
        """Test successful AnkiConnect API call."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"result": 1234}).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        # Mock json.load to return the expected result
        with patch('anki.json.load', return_value={"result": 1234}):
            result = anki.invoke_anki_connect("addNote", note={"deckName": "test"})
        
        # Check that the result is correct
        self.assertEqual(result, 1234)
        
        # Check that the request was made with the correct parameters
        mock_request.assert_called_once()
        mock_urlopen.assert_called_once()
    
    @patch('anki.urllib.request.urlopen')
    @patch('anki.urllib.request.Request')
    def test_invoke_anki_connect_error(self, mock_request, mock_urlopen):
        """Test AnkiConnect API call with error."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"error": "test error"}).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        # Mock json.load to return the expected result
        with patch('anki.json.load', return_value={"error": "test error"}):
            with self.assertRaises(Exception) as context:
                anki.invoke_anki_connect("addNote", note={"deckName": "test"})
        
        # Check that the exception message is correct
        self.assertEqual(str(context.exception), "test error")
    
    @patch('anki.os.getenv')
    @patch('anki.requests.post')
    def test_get_translation_success(self, mock_post, mock_getenv):
        """Test successful translation."""
        # Mock the environment variable
        mock_getenv.return_value = "test_api_key"
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello"}}]
        }
        mock_post.return_value = mock_response
        
        result = anki.get_translation("こんにちは")
        
        # Check that the result is correct
        self.assertEqual(result, "Hello")
        
        # Check that the request was made with the correct parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], anki.OPENAI_API_URL)
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test_api_key")
        self.assertIn("こんにちは", str(kwargs["json"]))
    
    @patch('anki.os.getenv')
    def test_get_translation_no_api_key(self, mock_getenv):
        """Test translation with no API key."""
        # Mock the environment variable
        mock_getenv.return_value = None
        
        with self.assertRaises(Exception) as context:
            anki.get_translation("こんにちは")
        
        # Check that the exception message is correct
        self.assertEqual(str(context.exception), anki.ERR_NO_API_KEY)
    
    @patch('anki.os.path.exists')
    @patch('anki.get_translation')
    @patch('anki.invoke_anki_connect')
    def test_add_sentence_card_with_api_translation(self, mock_invoke, mock_translate, mock_exists):
        """Test adding a sentence card to Anki with API translation."""
        # Mock the file existence check
        mock_exists.return_value = True
        
        # Mock the translation
        mock_translate.return_value = "Hello"
        
        # Mock the AnkiConnect API call
        mock_invoke.return_value = 1234
        
        # Mock open to avoid reading a real file
        with patch('builtins.open', mock_open(read_data=b'test audio data')):
            result = anki.add_sentence_card("test.mp3")
        
        # Check that the result is correct
        self.assertEqual(result, 1234)
        
        # Check that the translation was called
        mock_translate.assert_called_once_with("test")
        
        # Check that the AnkiConnect API was called
        mock_invoke.assert_called_once()
        args, kwargs = mock_invoke.call_args
        self.assertEqual(args[0], "addNote")
        self.assertEqual(kwargs["note"]["deckName"], anki.DEFAULT_DECK_NAME)
        self.assertEqual(kwargs["note"]["fields"]["Front"], "test")
        self.assertEqual(kwargs["note"]["fields"]["Back"], "Hello")
    
    @patch('anki.os.path.exists')
    @patch('anki.get_translation')
    @patch('anki.invoke_anki_connect')
    def test_add_sentence_card_with_custom_translation(self, mock_invoke, mock_translate, mock_exists):
        """Test adding a sentence card to Anki with custom translation."""
        # Mock the file existence check
        mock_exists.return_value = True
        
        # Mock the AnkiConnect API call
        mock_invoke.return_value = 1234
        
        # Mock open to avoid reading a real file
        with patch('builtins.open', mock_open(read_data=b'test audio data')):
            result = anki.add_sentence_card("test.mp3", custom_translation="Custom Hello")
        
        # Check that the result is correct
        self.assertEqual(result, 1234)
        
        # Check that the translation was NOT called
        mock_translate.assert_not_called()
        
        # Check that the AnkiConnect API was called with the custom translation
        mock_invoke.assert_called_once()
        args, kwargs = mock_invoke.call_args
        self.assertEqual(args[0], "addNote")
        self.assertEqual(kwargs["note"]["deckName"], anki.DEFAULT_DECK_NAME)
        self.assertEqual(kwargs["note"]["fields"]["Front"], "test")
        self.assertEqual(kwargs["note"]["fields"]["Back"], "Custom Hello")
    
    @patch('anki.add_sentence_card')
    def test_process_audio_files(self, mock_add_card):
        """Test processing multiple audio files."""
        # Mock the add_sentence_card function
        mock_add_card.side_effect = [1234, Exception("test error"), 5678]
        
        audio_files = ["test1.mp3", "test2.mp3", "test3.mp3"]
        successful, failed = anki.process_audio_files(audio_files)
        
        # Check that the successful and failed lists are correct
        self.assertEqual(successful, ["test1.mp3", "test3.mp3"])
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0][0], "test2.mp3")
        self.assertEqual(failed[0][1], "test error")
        
        # Check that add_sentence_card was called for each file
        self.assertEqual(mock_add_card.call_count, 3)
        
    @patch('anki.add_sentence_card')
    def test_process_audio_files_with_custom_translation(self, mock_add_card):
        """Test processing multiple audio files with custom translation."""
        # Mock the add_sentence_card function
        mock_add_card.side_effect = [1234, 5678]
        
        audio_files = ["test1.mp3", "test2.mp3"]
        successful, failed = anki.process_audio_files(
            audio_files, 
            custom_translation="Custom Hello"
        )
        
        # Check that the successful and failed lists are correct
        self.assertEqual(successful, ["test1.mp3", "test2.mp3"])
        self.assertEqual(len(failed), 0)
        
        # Check that add_sentence_card was called for each file with the custom translation
        self.assertEqual(mock_add_card.call_count, 2)
        for call_args in mock_add_card.call_args_list:
            self.assertEqual(call_args[1]["custom_translation"], "Custom Hello")


if __name__ == '__main__':
    unittest.main() 