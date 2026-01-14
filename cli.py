#!/usr/bin/env python3
import argparse
import os
import sys
import logging
from typing import List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args(args=None):
    """Parse command line arguments.
    
    Args:
        args: List of arguments to parse. Defaults to None, which uses sys.argv.
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="KotobaKit - Japanese Text-to-Speech and Anki Card Creator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute", required=True)
    
    # TTS command - only generates audio files
    tts_parser = subparsers.add_parser("tts", help="Generate TTS audio files only")
    tts_parser.add_argument("phrases", nargs="+", help="Japanese phrases to convert to speech")
    tts_parser.add_argument("-o", "--output-dir", help="Directory to save audio files")
    tts_parser.add_argument("--voice", help="Override TTS voice")
    tts_parser.add_argument("--speed", type=float, help="Override TTS speed")
    tts_parser.add_argument("--pitch", type=float, help="Override TTS pitch")
    
    # Card command - generates TTS and creates Anki cards
    card_parser = subparsers.add_parser("card", help="Generate TTS audio and create Anki cards")
    card_parser.add_argument("phrases", nargs="+", help="Japanese phrases to convert to speech")
    card_parser.add_argument("-o", "--output-dir", help="Directory to save audio files")
    
    # Default values without config dependency
    card_parser.add_argument("-d", "--deck", default="Japanese::Sentences", help="Anki deck name")
    card_parser.add_argument("-m", "--model", default="Basic", help="Anki note model name")
    card_parser.add_argument("-t", "--translation", help="Custom translation to use instead of API translation")
    card_parser.add_argument("--keep-audio", action="store_true", help="Keep audio files after adding to Anki")
    
    # Add override flags for OpenAI and other config values
    card_parser.add_argument("--openai-model", help="Override OpenAI model (e.g., gpt-3.5-turbo, gpt-4o)")
    card_parser.add_argument("--voice", help="Override TTS voice")
    card_parser.add_argument("--speed", type=float, help="Override TTS speed")
    card_parser.add_argument("--pitch", type=float, help="Override TTS pitch")
    
    # Config command - manage configuration
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument("--show", action="store_true", help="Show current configuration")
    config_parser.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), action="append", 
                              help="Set configuration value (e.g., --set anki.default_deck 'My Deck')")
    
    return parser.parse_args(args)


def run_tts_command(phrases: List[str], output_dir: Optional[str] = None,
                   voice: Optional[str] = None, speed: Optional[float] = None,
                   pitch: Optional[float] = None) -> List[str]:
    """Run the TTS command to generate audio files.

    Args:
        phrases: List of Japanese phrases to convert to speech
        output_dir: Optional directory to save files to
        voice: Optional TTS voice to use
        speed: Optional TTS speed to use
        pitch: Optional TTS pitch to use

    Returns:
        List of paths to the downloaded MP3 files

    Raises:
        Exception: If audio generation fails
    """
    from tts import TTSEngine

    logger.info(f"Generating TTS for {len(phrases)} phrases")

    # Create TTS config from parameters
    tts_config = {}
    if voice:
        tts_config['voice'] = voice
    if speed:
        tts_config['speed'] = speed
    if pitch:
        tts_config['pitch'] = pitch

    tts_engine = TTSEngine(tts_config if tts_config else None)

    audio_files = tts_engine.generate_audio(phrases, output_dir)

    logger.info(f"Successfully generated {len(audio_files)} audio files:")
    for file_path in audio_files:
        logger.info(f"  - {file_path}")

    return audio_files


def run_card_command(phrases: List[str], output_dir: Optional[str], deck_name: str,
                    model_name: str, custom_translation: Optional[str], keep_audio: bool,
                    openai_model: Optional[str] = None, voice: Optional[str] = None,
                    speed: Optional[float] = None, pitch: Optional[float] = None) -> bool:
    """Run the card command to generate TTS and add to Anki.

    Args:
        phrases: List of Japanese phrases to convert to speech
        output_dir: Optional directory to save files to
        deck_name: Name of the Anki deck to add the cards to
        model_name: Name of the Anki note model to use
        custom_translation: Optional custom translation to use instead of API translation
        keep_audio: If True, keep audio files after adding to Anki
        openai_model: Optional OpenAI model to use
        voice: Optional TTS voice to use
        speed: Optional TTS speed to use
        pitch: Optional TTS pitch to use

    Returns:
        True if all steps were successful, False otherwise

    Raises:
        Exception: If audio generation or card creation fails
    """
    from anki import AnkiConnector

    # Generate audio files (will raise exception on failure)
    audio_files = run_tts_command(phrases, output_dir, voice, speed, pitch)

    # Add to Anki
    logger.info(f"Adding {len(audio_files)} audio files to Anki")

    # Create AnkiConnector with optional model
    if openai_model:
        anki_connector = AnkiConnector(None, openai_model)
    else:
        anki_connector = AnkiConnector(None)

    successful_files, failed_files = anki_connector.process_audio_files(
        audio_files,
        deck_name=deck_name,
        model_name=model_name,
        custom_translation=custom_translation
    )

    # Print summary
    success_count = len(successful_files)
    failure_count = len(failed_files)
    logger.info(f"Summary: {success_count} cards added, {failure_count} errors")

    if failed_files:
        logger.error("Failed files:")
        for file, error in failed_files:
            logger.error(f"  {file}: {error}")

    # Clean up audio files if not keeping them
    if not keep_audio and success_count > 0:
        logger.info("Cleaning up audio files")
        for file_path in successful_files:
            try:
                os.remove(file_path)
                logger.info(f"Deleted: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {str(e)}")

    return failure_count == 0


