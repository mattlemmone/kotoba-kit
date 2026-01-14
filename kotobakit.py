#!/usr/bin/env python3
import sys
import logging
from typing import List, Optional, Any
from pathlib import Path
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import CLI functionality from cli.py
from cli import parse_args, run_tts_command, run_card_command


def main(cli_args=None):
    """Main entry point for the CLI.

    Args:
        cli_args: Optional list of command line arguments for testing.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_args(cli_args)

    try:
        if args.command == "tts":
            run_tts_command(
                args.phrases,
                args.output_dir,
                getattr(args, 'voice', None),
                getattr(args, 'speed', None),
                getattr(args, 'pitch', None)
            )
            success = True
        elif args.command == "card":
            # Pass model directly
            openai_model = getattr(args, 'openai_model', None)
            success = run_card_command(
                args.phrases,
                args.output_dir,
                args.deck,
                args.model,
                args.translation,
                args.keep_audio,
                openai_model,
                getattr(args, 'voice', None),
                getattr(args, 'speed', None),
                getattr(args, 'pitch', None)
            )
        else:
            # This should never happen due to required=True in subparsers
            print("Error: No command specified. Use --help for usage information.")
            return 1

        return 0 if success else 1

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 