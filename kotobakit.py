#!/usr/bin/env python3
import argparse
import os
import sys
import logging
from typing import List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import the config module, but don't fail if it doesn't exist yet
try:
    from config import Config
    config = Config()
except ImportError:
    config = None

# Import our modules
from tts import TTSEngine
from anki import AnkiConnector


def parse_args():
    """Parse command line arguments."""
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
    
    # Card command - generates TTS and creates Anki cards
    card_parser = subparsers.add_parser("card", help="Generate TTS audio and create Anki cards")
    card_parser.add_argument("phrases", nargs="+", help="Japanese phrases to convert to speech")
    card_parser.add_argument("-o", "--output-dir", help="Directory to save audio files")
    
    # Get default deck and model from config if available
    default_deck = config.get("anki", "default_deck") if config else "Japanese::Sentences"
    default_model = config.get("anki", "default_model") if config else "Basic"
    
    card_parser.add_argument("-d", "--deck", default=default_deck, help="Anki deck name")
    card_parser.add_argument("-m", "--model", default=default_model, help="Anki note model name")
    card_parser.add_argument("-t", "--translation", help="Custom translation to use instead of API translation")
    card_parser.add_argument("--keep-audio", action="store_true", help="Keep audio files after adding to Anki")
    
    # Config command - manage configuration
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument("--show", action="store_true", help="Show current configuration")
    config_parser.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), action="append", 
                              help="Set configuration value (e.g., --set anki.default_deck 'My Deck')")
    
    args = parser.parse_args()
    return args


def run_tts_command(phrases: List[str], output_dir: Optional[str] = None) -> List[str]:
    """Run the TTS command to generate audio files.
    
    Args:
        phrases: List of Japanese phrases to convert to speech
        output_dir: Optional directory to save files to
        
    Returns:
        List of paths to the downloaded MP3 files
    """
    logger.info(f"Generating TTS for {len(phrases)} phrases")
    
    # Use config if available
    tts_config = config.get("tts") if config else None
    tts_engine = TTSEngine(tts_config)
    
    audio_files = tts_engine.generate_audio(phrases, output_dir)
    
    if audio_files:
        logger.info(f"Successfully generated {len(audio_files)} audio files:")
        for file_path in audio_files:
            logger.info(f"  - {file_path}")
    else:
        logger.error("Failed to generate any audio files")
    
    return audio_files


def run_card_command(phrases: List[str], output_dir: Optional[str], deck_name: str, 
                    model_name: str, custom_translation: Optional[str], keep_audio: bool) -> bool:
    """Run the card command to generate TTS and add to Anki.
    
    Args:
        phrases: List of Japanese phrases to convert to speech
        output_dir: Optional directory to save files to
        deck_name: Name of the Anki deck to add the cards to
        model_name: Name of the Anki note model to use
        custom_translation: Optional custom translation to use instead of API translation
        keep_audio: If True, keep audio files after adding to Anki
        
    Returns:
        True if all steps were successful, False otherwise
    """
    # Generate audio files
    audio_files = run_tts_command(phrases, output_dir)
    if not audio_files:
        return False
    
    # Add to Anki
    logger.info(f"Adding {len(audio_files)} audio files to Anki")
    
    # Use config if available
    anki_config = config.get("anki") if config else None
    anki_connector = AnkiConnector(anki_config)
    
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


def run_config_command(show: bool, set_values: Optional[List[List[str]]]) -> bool:
    """Run the config command to manage configuration.
    
    Args:
        show: If True, show the current configuration
        set_values: List of [key, value] pairs to set in the configuration
        
    Returns:
        True if all steps were successful, False otherwise
    """
    from config import Config
    config = Config()
    
    if show:
        import json
        print(json.dumps(config.config, indent=2))
    
    if set_values:
        for key_path, value in set_values:
            # Convert string value to appropriate type
            if value.lower() == "true":
                typed_value = True
            elif value.lower() == "false":
                typed_value = False
            elif value.isdigit():
                typed_value = int(value)
            elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
                typed_value = float(value)
            else:
                typed_value = value
            
            # Split key path and set value
            keys = key_path.split(".")
            current = config.config
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = typed_value
        
        config.save()
        logger.info("Configuration saved")
    
    return True


def main():
    """Main entry point for the CLI."""
    args = parse_args()
    
    if args.command == "tts":
        success = bool(run_tts_command(args.phrases, args.output_dir))
    elif args.command == "card":
        success = run_card_command(
            args.phrases, 
            args.output_dir, 
            args.deck, 
            args.model, 
            args.translation, 
            args.keep_audio
        )
    elif args.command == "config":
        success = run_config_command(args.show, args.set)
    else:
        # This should never happen due to required=True in subparsers
        print("Error: No command specified. Use --help for usage information.")
        return 1
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 