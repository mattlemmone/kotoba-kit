# KotobaKit

A command-line tool that generates Japanese text-to-speech audio and creates Anki flashcards.

## Features

- Generate MP3 audio files from Japanese text using a free TTS service
- Create Anki flashcards with Japanese text, English translation, and audio
- Translate Japanese text to English using OpenAI's GPT API
- Flexible CLI with options to:
  - Generate audio files only
  - Generate audio and create Anki cards in one step

## Requirements

- Python 3.6+
- Anki with [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on installed
- OpenAI API key (for translation)

## Installation

1. Clone this repository:

   ```
   git clone https://github.com/yourusername/kotobakit.git
   cd kotobakit
   ```

2. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Set your OpenAI API key as an environment variable:
   ```
   export OPENAI_API_KEY=your_api_key_here
   ```

## Usage

The application provides two main commands:

### Generate TTS Audio Only

```
python kotobakit.py tts "こんにちは" "ありがとう" -o ./audio
```

This will generate MP3 files for the Japanese phrases "こんにちは" and "ありがとう" in the `./audio` directory without creating Anki cards.

### Generate TTS and Create Anki Cards

```
python kotobakit.py card "こんにちは" "ありがとう" -d "Japanese::Sentences" --keep-audio
```

This will generate MP3 files for the Japanese phrases, add them to Anki, and keep the audio files (by default, they are deleted after adding to Anki).

### Using Custom Translations

By default, the application uses OpenAI's API to translate Japanese text to English. You can provide your own translation with the `-t` or `--translation` option:

```
python kotobakit.py card "こんにちは" -t "Hello"
```

This is useful when you want to:

- Provide a more accurate or contextual translation
- Save API calls to OpenAI
- Add nuance or notes to the translation

## Command-Line Options

### Global Options

- `--help`: Show help message and exit

### TTS Command Options

- `phrases`: One or more Japanese phrases to convert to speech
- `-o, --output-dir`: Directory to save audio files (default: current directory)

### Card Command Options

- `phrases`: One or more Japanese phrases to convert to speech
- `-o, --output-dir`: Directory to save audio files (default: current directory)
- `-d, --deck`: Anki deck name (default: "Japanese::Sentences")
- `-m, --model`: Anki note model name (default: "Basic")
- `-t, --translation`: Custom translation to use instead of API translation
- `--keep-audio`: Keep audio files after adding to Anki

## How It Works

1. The TTS functionality uses the ondoku3.com service to generate high-quality Japanese speech
2. The Anki integration uses the AnkiConnect add-on to add cards to your Anki collection
3. Translation is performed using OpenAI's GPT API

## Running Tests

To run the tests:

```
python -m unittest discover
```

## License

MIT

## Acknowledgements

This project is a Python CLI rewrite of the original JavaScript implementation.
