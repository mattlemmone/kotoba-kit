#!/usr/bin/env python3
import sys
import logging
from typing import List, Optional, Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import CLI functionality from cli.py
from cli import parse_args, run_tts_command, run_card_command, run_config_command


def main(cli_args=None):
    """Main entry point for the CLI.
    
    Args:
        cli_args: Optional list of command line arguments for testing.
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_args(cli_args)
    
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