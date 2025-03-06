import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
import json

import anki
from anki import AnkiConnector


class TestAnki(unittest.TestCase):
    
    def test_build_anki_connect_action(self):
        """Test that the AnkiConnect action is built correctly."""
        action = "addNote"
        params = {"note": {"deckName": "test", "modelName": "test"}}
        
        connector = AnkiConnector()
        result = connector.build_action(action, **params)
        
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
            connector = AnkiConnector()
            result = connector.invoke("addNote", note={"deckName": "test"})
        
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
            connector = AnkiConnector()
            with self.assertRaises(Exception) as context:
                connector.invoke("addNote", note={"deckName": "test"})
        
        # Check that the exception message is correct
        self.assertEqual(str(context.exception), "test error")
    
    @patch('translator.Translator.translate')
    def test_get_translation_success(self, mock_translate):
        """Test successful translation."""
        # Mock the translation
        mock_translate.return_value = "Hello"
        
        connector = AnkiConnector()
        result = connector.translator.translate("こんにちは")
        
        # Check that the result is correct
        self.assertEqual(result, "Hello")
        
        # Check that the translation was called
        mock_translate.assert_called_once_with("こんにちは")
    
    @patch('translator.Translator.translate')
    def test_get_translation_no_api_key(self, mock_translate):
        """Test translation with no API key."""
        # Mock the translation to raise an exception
        mock_translate.side_effect = Exception("OpenAI API key not found. Set the OPENAI_API_KEY environment variable.")
        
        connector = AnkiConnector()
        with self.assertRaises(Exception) as context:
            connector.translator.translate("こんにちは")
        
        # Check that the exception message is correct
        self.assertEqual(str(context.exception), "OpenAI API key not found. Set the OPENAI_API_KEY environment variable.")
    
    @patch('anki.os.path.exists')
    @patch('translator.Translator.translate')
    @patch('anki.AnkiConnector.invoke')
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
            connector = AnkiConnector()
            result = connector.add_sentence_card("test.mp3")
        
        # Check that the result is correct
        self.assertEqual(result, 1234)
        
        # Check that the translation was called
        mock_translate.assert_called_once_with("test")
        
        # Check that the AnkiConnect API was called
        mock_invoke.assert_called_once()
        args, kwargs = mock_invoke.call_args
        self.assertEqual(args[0], "addNote")
        self.assertEqual(kwargs["note"]["deckName"], "Japanese::Sentences")
        self.assertEqual(kwargs["note"]["fields"]["Front"], "test")
        self.assertEqual(kwargs["note"]["fields"]["Back"], "Hello")
    
    @patch('anki.os.path.exists')
    @patch('translator.Translator.translate')
    @patch('anki.AnkiConnector.invoke')
    def test_add_sentence_card_with_custom_translation(self, mock_invoke, mock_translate, mock_exists):
        """Test adding a sentence card to Anki with custom translation."""
        # Mock the file existence check
        mock_exists.return_value = True
        
        # Mock the AnkiConnect API call
        mock_invoke.return_value = 1234
        
        # Mock open to avoid reading a real file
        with patch('builtins.open', mock_open(read_data=b'test audio data')):
            connector = AnkiConnector()
            result = connector.add_sentence_card("test.mp3", custom_translation="Custom Hello")
        
        # Check that the result is correct
        self.assertEqual(result, 1234)
        
        # Check that the translation was NOT called
        mock_translate.assert_not_called()
        
        # Check that the AnkiConnect API was called with the custom translation
        mock_invoke.assert_called_once()
        args, kwargs = mock_invoke.call_args
        self.assertEqual(args[0], "addNote")
        self.assertEqual(kwargs["note"]["deckName"], "Japanese::Sentences")
        self.assertEqual(kwargs["note"]["fields"]["Front"], "test")
        self.assertEqual(kwargs["note"]["fields"]["Back"], "Custom Hello")
    
    @patch('anki.AnkiConnector.add_sentence_card')
    def test_process_audio_files(self, mock_add_card):
        """Test processing multiple audio files."""
        # Mock the add_sentence_card function
        mock_add_card.side_effect = [1234, Exception("test error"), 5678]
        
        connector = AnkiConnector()
        audio_files = ["test1.mp3", "test2.mp3", "test3.mp3"]
        successful, failed = connector.process_audio_files(audio_files)
        
        # Check that the successful and failed lists are correct
        self.assertEqual(successful, ["test1.mp3", "test3.mp3"])
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0][0], "test2.mp3")
        self.assertEqual(failed[0][1], "test error")
        
        # Check that add_sentence_card was called for each file
        self.assertEqual(mock_add_card.call_count, 3)
        
    @patch('anki.AnkiConnector.add_sentence_card')
    def test_process_audio_files_with_custom_translation(self, mock_add_card):
        """Test processing multiple audio files with custom translation."""
        # Mock the add_sentence_card function
        mock_add_card.side_effect = [1234, 5678]
        
        connector = AnkiConnector()
        audio_files = ["test1.mp3", "test2.mp3"]
        successful, failed = connector.process_audio_files(
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