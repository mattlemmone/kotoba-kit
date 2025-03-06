import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from translator import Translator

class TestTranslator(unittest.TestCase):
    
    def setUp(self):
        self.translator = Translator()
        self.test_text = "こんにちは"
    
    @patch('translator.requests.post')
    def test_translate(self, mock_post):
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Hello'}}]
        }
        mock_post.return_value = mock_response
        
        # Set environment variable for test
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            result = self.translator.translate(self.test_text)
        
        self.assertEqual(result, 'Hello')
        mock_post.assert_called_once() 