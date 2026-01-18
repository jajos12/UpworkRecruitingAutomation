"""Configuration loader for YAML files."""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import os
from dotenv import load_dotenv

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class UpworkConfig:
    """Upwork API configuration."""

    client_id: str
    client_secret: str
    access_token: str
    refresh_token: str
    refresh_interval_minutes: int = 15
    max_retries: int = 3
    rate_limit_delay_seconds: int = 2


@dataclass
class AIConfig:
    """AI analysis configuration."""

    api_key: str
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 2000
    tier1_threshold: int = 85
    tier2_threshold: int = 70


@dataclass
class GoogleSheetsConfig:
    """Google Sheets configuration."""

    credentials_path: str
    spreadsheet_id: str


@dataclass
class CommunicationConfig:
    """Communication automation configuration."""

    auto_respond_tier1: bool = True
    follow_up_after_hours: int = 48
    batch_decline_tier3: bool = True
    calendly_link: str = ""


@dataclass
class NotificationConfig:
    """Notification configuration."""

    slack_webhook: Optional[str] = None
    email_alerts: bool = False


@dataclass
class AppConfig:
    """Main application configuration."""

    upwork: UpworkConfig
    ai: AIConfig
    google_sheets: GoogleSheetsConfig
    communication: CommunicationConfig
    notifications: NotificationConfig
    environment: str = "development"
    debug: bool = False


@dataclass
class JobCriteria:
    """Hiring criteria for a specific job."""

    job_id: str
    job_title: str
    must_have: List[str]
    nice_to_have: List[Dict[str, Any]]
    red_flags: List[str]


class ConfigLoader:
    """Loads and validates configuration from YAML files and environment variables."""

    def __init__(self, config_dir: str = "config"):
        """
        Initialize config loader.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        load_dotenv()  # Load environment variables from .env file

    def load_app_config(self) -> AppConfig:
        """
        Load main application configuration.

        Returns:
            AppConfig instance

        Raises:
            FileNotFoundError: If settings.yaml not found
            ValueError: If required environment variables missing
        """
        logger.info("Loading application configuration...")

        # Load settings.yaml
        settings_file = self.config_dir / "settings.yaml"
        if not settings_file.exists():
            raise FileNotFoundError(f"Settings file not found: {settings_file}")

        with open(settings_file, "r") as f:
            settings = yaml.safe_load(f)

        # Load environment variables
        upwork_config = UpworkConfig(
            client_id=self._get_env("UPWORK_CLIENT_ID"),
            client_secret=self._get_env("UPWORK_CLIENT_SECRET"),
            access_token=self._get_env("UPWORK_ACCESS_TOKEN"),
            refresh_token=self._get_env("UPWORK_REFRESH_TOKEN"),
            refresh_interval_minutes=settings.get("upwork", {}).get(
                "refresh_interval_minutes", 15
            ),
            max_retries=settings.get("upwork", {}).get("max_retries", 3),
            rate_limit_delay_seconds=settings.get("upwork", {}).get(
                "rate_limit_delay_seconds", 2
            ),
        )

        ai_config = AIConfig(
            api_key=self._get_env("ANTHROPIC_API_KEY"),
            model=settings.get("ai", {}).get("model", "claude-sonnet-4-20250514"),
            max_tokens=settings.get("ai", {}).get("max_tokens", 2000),
            tier1_threshold=settings.get("ai", {}).get("tier1_threshold", 85),
            tier2_threshold=settings.get("ai", {}).get("tier2_threshold", 70),
        )

        google_sheets_config = GoogleSheetsConfig(
            credentials_path=self._get_env("GOOGLE_SHEETS_CREDENTIALS_PATH"),
            spreadsheet_id=self._get_env("GOOGLE_SPREADSHEET_ID"),
        )

        communication_config = CommunicationConfig(
            auto_respond_tier1=settings.get("communication", {}).get(
                "auto_respond_tier1", True
            ),
            follow_up_after_hours=settings.get("communication", {}).get(
                "follow_up_after_hours", 48
            ),
            batch_decline_tier3=settings.get("communication", {}).get(
                "batch_decline_tier3", True
            ),
            calendly_link=os.getenv("CALENDLY_LINK", ""),
        )

        notification_config = NotificationConfig(
            slack_webhook=os.getenv("SLACK_WEBHOOK_URL"),
            email_alerts=settings.get("notifications", {}).get("email_alerts", False),
        )

        app_config = AppConfig(
            upwork=upwork_config,
            ai=ai_config,
            google_sheets=google_sheets_config,
            communication=communication_config,
            notifications=notification_config,
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )

        logger.info("Configuration loaded successfully")
        return app_config

    def load_job_criteria(self, job_id: str) -> Optional[JobCriteria]:
        """
        Load hiring criteria for a specific job.

        Args:
            job_id: Job ID or filename (without .yaml extension)

        Returns:
            JobCriteria instance or None if not found
        """
        criteria_dir = self.config_dir / "criteria"
        criteria_file = criteria_dir / f"{job_id}.yaml"

        if not criteria_file.exists():
            logger.warning(f"Criteria file not found: {criteria_file}")
            return None

        logger.info(f"Loading criteria for job: {job_id}")

        with open(criteria_file, "r") as f:
            data = yaml.safe_load(f)

        return JobCriteria(
            job_id=data["job_id"],
            job_title=data["job_title"],
            must_have=data.get("must_have", []),
            nice_to_have=data.get("nice_to_have", []),
            red_flags=data.get("red_flags", []),
        )

    def load_all_job_criteria(self) -> List[JobCriteria]:
        """
        Load all job criteria files from the criteria directory.

        Returns:
            List of JobCriteria instances
        """
        criteria_dir = self.config_dir / "criteria"
        if not criteria_dir.exists():
            logger.warning(f"Criteria directory not found: {criteria_dir}")
            return []

        criteria_list = []
        for criteria_file in criteria_dir.glob("*.yaml"):
            if criteria_file.name == "example_job.yaml":
                continue  # Skip example file

            job_id = criteria_file.stem
            criteria = self.load_job_criteria(job_id)
            if criteria:
                criteria_list.append(criteria)

        logger.info(f"Loaded {len(criteria_list)} job criteria files")
        return criteria_list

    def load_message_template(self, template_name: str) -> str:
        """
        Load a message template.

        Args:
            template_name: Template name (e.g., 'initial_outreach', 'follow_up')

        Returns:
            Template content as string

        Raises:
            FileNotFoundError: If template not found
        """
        template_dir = self.config_dir / "templates"
        template_file = template_dir / f"{template_name}.txt"

        if not template_file.exists():
            raise FileNotFoundError(f"Template not found: {template_file}")

        with open(template_file, "r") as f:
            return f.read()

    def _get_env(self, key: str) -> str:
        """
        Get environment variable or raise error if not set.

        Args:
            key: Environment variable name

        Returns:
            Environment variable value

        Raises:
            ValueError: If environment variable not set
        """
        value = os.getenv(key)
        if value is None:
            raise ValueError(
                f"Required environment variable not set: {key}. "
                f"Please check your .env file."
            )
        return value


def validate_config(config: AppConfig) -> bool:
    """
    Validate configuration.

    Args:
        config: Application configuration

    Returns:
        True if valid, False otherwise
    """
    logger.info("Validating configuration...")

    errors = []

    # Validate Upwork config
    if not config.upwork.client_id:
        errors.append("Upwork client_id is required")
    if not config.upwork.client_secret:
        errors.append("Upwork client_secret is required")
    if not config.upwork.access_token:
        errors.append("Upwork access_token is required")

    # Validate AI config
    if not config.ai.api_key:
        errors.append("Anthropic API key is required")

    # Validate Google Sheets config
    if not config.google_sheets.credentials_path:
        errors.append("Google Sheets credentials_path is required")
    elif not Path(config.google_sheets.credentials_path).exists():
        errors.append(
            f"Google Sheets credentials file not found: {config.google_sheets.credentials_path}"
        )

    if not config.google_sheets.spreadsheet_id:
        errors.append("Google Sheets spreadsheet_id is required")

    # Validate thresholds
    if config.ai.tier1_threshold <= config.ai.tier2_threshold:
        errors.append("tier1_threshold must be greater than tier2_threshold")

    if errors:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return False

    logger.info("Configuration validation passed")
    return True
