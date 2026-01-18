#!/usr/bin/env python3
"""
Upwork Hire Bot - AI-powered automation for Upwork hiring.

Main entry point for the application.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logger
from src.utils.config_loader import ConfigLoader, validate_config
from src.upwork_client import UpworkClient
from src.ai_analyzer import AIAnalyzer
from src.sheets_manager import SheetsManager
from src.communicator import Communicator
from src.pipeline import Pipeline
from src.scheduler import run_daemon

# Initialize logger
logger = setup_logger("upwork_hire_bot", level="INFO")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Upwork Hire Bot - Automate your Upwork hiring process",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Run full pipeline once
  %(prog)s --daemon                  # Run continuously (every 15 minutes)
  %(prog)s --fetch-only              # Only fetch data from Upwork
  %(prog)s --analyze-only            # Only analyze existing data
  %(prog)s --dry-run                 # Show what would happen without sending messages
  %(prog)s --help                    # Show this help message

For more information, see README.md
        """,
    )

    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously as a daemon (checks every 15 minutes)",
    )

    parser.add_argument(
        "--fetch-only",
        action="store_true",
        help="Only fetch data from Upwork, skip analysis and communication",
    )

    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Only analyze existing data, skip fetch and communication",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without actually sending messages (safe for testing)",
    )

    parser.add_argument(
        "--config-dir",
        type=str,
        default="config",
        help="Path to configuration directory (default: config)",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=15,
        help="Interval in minutes for daemon mode (default: 15)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    return parser.parse_args()


def initialize_components(config_loader):
    """
    Initialize all system components.

    Args:
        config_loader: ConfigLoader instance

    Returns:
        Tuple of (upwork_client, ai_analyzer, sheets_manager, communicator, pipeline)
    """
    logger.info("Initializing system components...")

    # Load configuration
    config = config_loader.load_app_config()

    # Validate configuration
    if not validate_config(config):
        logger.error("Configuration validation failed. Please check your settings.")
        sys.exit(1)

    # Initialize Upwork client
    logger.info("Connecting to Upwork API...")
    upwork_client = UpworkClient(config.upwork)

    # Initialize Google Sheets
    logger.info("Connecting to Google Sheets...")
    sheets_manager = SheetsManager(config.google_sheets)

    # Initialize AI analyzer
    logger.info("Initializing AI analyzer...")
    ai_analyzer = AIAnalyzer(config.ai)

    # Initialize communicator
    logger.info("Initializing communicator...")
    communicator = Communicator(
        upwork_client=upwork_client,
        sheets_manager=sheets_manager,
        config=config.communication,
        ai_api_key=config.ai.api_key,
        config_loader=config_loader,
    )

    # Initialize pipeline
    logger.info("Initializing pipeline...")
    pipeline = Pipeline(
        upwork_client=upwork_client,
        ai_analyzer=ai_analyzer,
        sheets_manager=sheets_manager,
        communicator=communicator,
        config_loader=config_loader,
    )

    logger.info("✅ All components initialized successfully\n")

    return upwork_client, ai_analyzer, sheets_manager, communicator, pipeline


def main():
    """Main entry point."""
    args = parse_args()

    # Set log level
    if args.debug:
        import logging
        logging.getLogger("upwork_hire_bot").setLevel(logging.DEBUG)

    # Print banner
    logger.info("=" * 80)
    logger.info("🤖  UPWORK HIRE BOT - AI-Powered Hiring Automation")
    logger.info("=" * 80)
    logger.info("")

    try:
        # Initialize config loader
        config_loader = ConfigLoader(config_dir=args.config_dir)

        # Initialize all components
        upwork_client, ai_analyzer, sheets_manager, communicator, pipeline = (
            initialize_components(config_loader)
        )

        # Determine what to run
        if args.daemon:
            # Run as daemon
            logger.info("🚀 Starting daemon mode...")
            logger.info(f"Pipeline will run every {args.interval} minutes")
            logger.info("Press Ctrl+C to stop\n")

            run_daemon(pipeline, interval_minutes=args.interval)

        else:
            # Run once
            logger.info("🚀 Running pipeline once...\n")

            # Determine pipeline phases
            fetch = not args.analyze_only
            analyze = not args.fetch_only
            communicate = not (args.fetch_only or args.analyze_only)

            # Run pipeline
            stats = pipeline.run_full_pipeline(
                fetch=fetch,
                analyze=analyze,
                communicate=communicate,
                dry_run=args.dry_run,
            )

            # Print final message
            if args.dry_run:
                logger.info("\n✅ DRY RUN complete. No actual changes were made.")
            else:
                logger.info("\n✅ Pipeline complete! Check your Google Sheet for results.")

            logger.info("")

    except KeyboardInterrupt:
        logger.info("\n\n👋 Interrupted by user. Shutting down...")
        sys.exit(0)

    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=args.debug)
        sys.exit(1)

    finally:
        # Cleanup
        try:
            if 'upwork_client' in locals():
                upwork_client.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
