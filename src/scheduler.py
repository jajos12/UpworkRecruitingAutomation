"""Background scheduler for automated pipeline execution."""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import signal
import sys

from src.pipeline import Pipeline
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PipelineScheduler:
    """
    Schedules and runs the pipeline at regular intervals.

    Features:
    - Runs pipeline every N minutes
    - Graceful shutdown handling
    - Error recovery
    """

    def __init__(self, pipeline: Pipeline, interval_minutes: int = 15):
        """
        Initialize scheduler.

        Args:
            pipeline: Pipeline instance to run
            interval_minutes: How often to run the pipeline
        """
        self.pipeline = pipeline
        self.interval_minutes = interval_minutes
        self.scheduler = BlockingScheduler()
        self.running = False

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info(f"Scheduler initialized (interval: {interval_minutes} minutes)")

    def start(self, run_immediately: bool = True):
        """
        Start the scheduler.

        Args:
            run_immediately: If True, run pipeline once immediately before scheduling
        """
        logger.info("Starting scheduler...")

        # Run once immediately if requested
        if run_immediately:
            logger.info("Running initial pipeline execution...")
            self._run_pipeline_safe()

        # Schedule recurring runs
        self.scheduler.add_job(
            func=self._run_pipeline_safe,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id="pipeline_job",
            name="Run Upwork Hiring Pipeline",
            replace_existing=True,
        )

        self.running = True

        logger.info(f"Scheduler started. Pipeline will run every {self.interval_minutes} minutes.")
        logger.info("Press Ctrl+C to stop.")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler interrupted")
            self.stop()

    def stop(self):
        """Stop the scheduler gracefully."""
        if self.running:
            logger.info("Stopping scheduler...")
            self.scheduler.shutdown(wait=True)
            self.running = False
            logger.info("Scheduler stopped")

    def _run_pipeline_safe(self):
        """Run pipeline with error handling."""
        try:
            logger.info("\n" + "🤖 " * 30)
            logger.info(f"Pipeline execution started at {datetime.now()}")
            logger.info("🤖 " * 30 + "\n")

            stats = self.pipeline.run_full_pipeline(
                fetch=True,
                analyze=True,
                communicate=True,
                dry_run=False,
            )

            logger.info(f"\n✅ Pipeline completed successfully")
            logger.info(f"Next run scheduled in {self.interval_minutes} minutes\n")

        except Exception as e:
            logger.error(f"❌ Pipeline execution failed: {e}", exc_info=True)
            logger.info(f"Will retry in {self.interval_minutes} minutes\n")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"\nReceived signal {signum}, shutting down gracefully...")
        self.stop()
        sys.exit(0)


def run_daemon(pipeline: Pipeline, interval_minutes: int = 15):
    """
    Run pipeline as a daemon with scheduled execution.

    Args:
        pipeline: Pipeline instance
        interval_minutes: How often to run the pipeline
    """
    scheduler = PipelineScheduler(pipeline, interval_minutes)
    scheduler.start(run_immediately=True)
