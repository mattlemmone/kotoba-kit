#!/usr/bin/env python3
import argparse
import os
import sys
import logging
from typing import List, Optional

import tts
import anki

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
    card_parser.add_argument("-d", "--deck", default=anki.DEFAULT_DECK_NAME, help="Anki deck name")
    card_parser.add_argument("-m", "--model", default=anki.DEFAULT_MODEL_NAME, help="Anki note model name")
    card_parser.add_argument("-t", "--translation", help="Custom translation to use instead of API translation")
    card_parser.add_argument("--keep-audio", action="store_true", help="Keep audio files after adding to Anki")
    
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
    audio_files = tts.generate_audio(phrases, output_dir)
    
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
    successful_files, failed_files = anki.process_audio_files(
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
    else:
        # This should never happen due to required=True in subparsers
        print("Error: No command specified. Use --help for usage information.")
        return 1
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 