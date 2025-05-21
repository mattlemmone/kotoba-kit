import unittest
import sys
import tempfile
from unittest.mock import patch, MagicMock

import kotobakit
from tts import TTSEngine
from anki import AnkiConnector
import cli


class TestKotobaKit(unittest.TestCase):
    """Test cases for the kotobakit module."""

    @patch('tts.TTSEngine.generate_audio')
    def test_run_tts_command(self, mock_generate):
        """Test the TTS command."""
        # Mock the generate_audio function
        mock_generate.return_value = ["/tmp/test.mp3"]
        
        # Call the function
        result = cli.run_tts_command(["test"], "/tmp")
        
        # Check that generate_audio was called with the right parameters
        mock_generate.assert_called_once_with(["test"], "/tmp")
        
        # Check that the result is correct
        self.assertEqual(result, ["/tmp/test.mp3"])

    @patch('cli.run_tts_command')
    @patch('anki.AnkiConnector')
    def test_run_card_command_success(self, mock_anki, mock_tts):
        """Test the card command with successful TTS."""
        # Mock the TTS command
        mock_tts.return_value = ["/tmp/test.mp3"]
        
        # Mock the AnkiConnector instance
        mock_anki_instance = mock_anki.return_value
        mock_anki_instance.process_audio_files.return_value = (["test.mp3"], [])
        
        # Call the function
        result = cli.run_card_command(
            ["test"], 
            "/tmp", 
            "test_deck", 
            "test_model", 
            None, 
            False
        )
        
        # Check that run_tts_command was called with the right parameters
        mock_tts.assert_called_once_with(["test"], "/tmp")
        
        # Check that process_audio_files was called with the right parameters
        mock_anki_instance.process_audio_files.assert_called_once_with(
            ["/tmp/test.mp3"], 
            deck_name="test_deck", 
            model_name="test_model", 
            custom_translation=None
        )
        
        # Check that the result is True
        self.assertTrue(result)

    @patch('cli.run_tts_command')
    @patch('anki.AnkiConnector')
    def test_run_card_command_with_custom_translation(self, mock_anki, mock_tts):
        """Test the card command with a custom translation."""
        # Mock the TTS command
        mock_tts.return_value = ["/tmp/test.mp3"]
        
        # Mock the AnkiConnector instance
        mock_anki_instance = mock_anki.return_value
        mock_anki_instance.process_audio_files.return_value = (["test.mp3"], [])
        
        # Call the function
        result = cli.run_card_command(
            ["test"], 
            "/tmp", 
            "test_deck", 
            "test_model", 
            "Custom Hello", 
            False
        )
        
        # Check that run_tts_command was called with the right parameters
        mock_tts.assert_called_once_with(["test"], "/tmp")
        
        # Check that process_audio_files was called with the right parameters
        mock_anki_instance.process_audio_files.assert_called_once_with(
            ["/tmp/test.mp3"], 
            deck_name="test_deck", 
            model_name="test_model", 
            custom_translation="Custom Hello"
        )
        
        # Check that the result is True
        self.assertTrue(result)

    @patch('cli.run_tts_command')
    def test_run_card_command_tts_failure(self, mock_tts):
        """Test the card command when TTS fails."""
        # Mock the TTS command to return an empty list (failure)
        mock_tts.return_value = []
        
        # Call the function
        result = cli.run_card_command(
            ["test"], 
            "/tmp", 
            "test_deck", 
            "test_model", 
            None, 
            False
        )
        
        # Check that the result is False
        self.assertFalse(result)

    def test_main_tts(self):
        """Test the main function with TTS command."""
        with patch('kotobakit.parse_args') as mock_parse_args:
            # Create mock args
            mock_args = MagicMock()
            mock_args.command = "tts"
            mock_args.phrases = ["こんにちは"]
            mock_args.output_dir = "/tmp"
            mock_parse_args.return_value = mock_args
            
            # Mock the TTS command function
            with patch('kotobakit.run_tts_command', return_value=["/tmp/test.mp3"]) as mock_tts:
                # Call the function
                result = kotobakit.main()
                
                # Check that run_tts_command was called with the right parameters
                mock_tts.assert_called_once_with(["こんにちは"], "/tmp")
                
                # Check that the result is 0 (success)
                self.assertEqual(result, 0)

    def test_main_card(self):
        """Test the main function with card command."""
        with patch('kotobakit.parse_args') as mock_parse_args:
            # Create mock args
            mock_args = MagicMock()
            mock_args.command = "card"
            mock_args.phrases = ["こんにちは"]
            mock_args.output_dir = "/tmp"
            mock_args.deck = "test_deck"
            mock_args.model = "test_model"
            mock_args.translation = "Custom Hello"
            mock_args.keep_audio = True
            mock_parse_args.return_value = mock_args
            
            # Mock the card command function
            with patch('kotobakit.run_card_command', return_value=True) as mock_card:
                # Call the function
                result = kotobakit.main()
                
                # Check that run_card_command was called with the right parameters
                mock_card.assert_called_once_with(
                    ["こんにちは"], 
                    "/tmp", 
                    "test_deck", 
                    "test_model", 
                    "Custom Hello", 
                    True
                )
                
                # Check that the result is 0 (success)
                self.assertEqual(result, 0)

    def test_main_error_no_command(self):
        """Test error handling when the command would be missing."""
        with patch('kotobakit.parse_args') as mock_parse_args:
            # Create mock args
            mock_args = MagicMock()
            mock_args.command = None
            mock_parse_args.return_value = mock_args
            
            # Capture stdout
            original_stdout = sys.stdout
            try:
                with tempfile.TemporaryFile(mode='w+') as temp_stdout:
                    sys.stdout = temp_stdout
                    
                    result = kotobakit.main()
                    
                    # Check that the result is 1 (failure)
                    self.assertEqual(result, 1)
                    
                    # Check that the error message was printed
                    temp_stdout.seek(0)
                    output = temp_stdout.read()
                    self.assertIn("Error: No command specified", output)
            finally:
                sys.stdout = original_stdout


if __name__ == '__main__':
    unittest.main() 