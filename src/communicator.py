"""Communication manager for automated messaging with applicants."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from anthropic import Anthropic

from src.upwork_client import UpworkClient
from src.sheets_manager import SheetsManager
from src.utils.logger import get_logger
from src.utils.config_loader import CommunicationConfig, ConfigLoader

logger = get_logger(__name__)


class Communicator:
    """
    Manages automated communication with applicants.

    Features:
    - Auto-respond to Tier 1 candidates
    - Personalized message generation
    - Follow-up scheduling
    - Batch decline for Tier 3
    """

    def __init__(
        self,
        upwork_client: UpworkClient,
        sheets_manager: SheetsManager,
        config: CommunicationConfig,
        ai_api_key: str,
        config_loader: ConfigLoader,
    ):
        """
        Initialize communicator.

        Args:
            upwork_client: Upwork API client
            sheets_manager: Google Sheets manager
            config: Communication configuration
            ai_api_key: Anthropic API key for message generation
            config_loader: Config loader for templates
        """
        self.upwork = upwork_client
        self.sheets = sheets_manager
        self.config = config
        self.config_loader = config_loader
        self.ai_client = Anthropic(api_key=ai_api_key)
        logger.info("Communicator initialized")

    def process_tier1_candidates(self, dry_run: bool = False) -> int:
        """
        Send initial outreach to all Tier 1 candidates who haven't been contacted.

        Args:
            dry_run: If True, log what would be sent but don't actually send

        Returns:
            Number of messages sent
        """
        logger.info("Processing Tier 1 candidates for outreach...")

        if not self.config.auto_respond_tier1:
            logger.info("Auto-respond for Tier 1 is disabled")
            return 0

        candidates = self.sheets.get_tier1_candidates()
        messages_sent = 0

        for candidate in candidates:
            try:
                # Generate personalized message
                message = self._generate_initial_outreach(candidate)

                if dry_run:
                    logger.info(f"[DRY RUN] Would send to {candidate.get('applicant_name')}:")
                    logger.info(f"Message: {message}")
                    messages_sent += 1
                else:
                    # Get room ID (proposal ID can be used as room ID in some cases)
                    # Note: Actual implementation may need to fetch room ID differently
                    room_id = candidate.get("proposal_id")

                    if not room_id:
                        logger.warning(
                            f"No room ID for {candidate.get('applicant_name')}, skipping"
                        )
                        continue

                    # Send message
                    success = self.upwork.send_message(room_id, message)

                    if success:
                        # Update status in sheets
                        self.sheets.update_status(
                            job_title=candidate.get("job_title"),
                            proposal_id=candidate.get("proposal_id"),
                            status="CONTACTED",
                            notes="Sent initial outreach (auto)",
                        )
                        messages_sent += 1
                        logger.info(
                            f"Sent initial outreach to {candidate.get('applicant_name')}"
                        )
                    else:
                        logger.error(
                            f"Failed to send message to {candidate.get('applicant_name')}"
                        )

            except Exception as e:
                logger.error(
                    f"Error processing candidate {candidate.get('applicant_name')}: {e}"
                )

        logger.info(f"Tier 1 outreach complete: {messages_sent} messages sent")
        return messages_sent

    def process_followups(self, dry_run: bool = False) -> int:
        """
        Send follow-up messages to candidates who haven't responded.

        Args:
            dry_run: If True, log what would be sent but don't actually send

        Returns:
            Number of follow-ups sent
        """
        logger.info("Processing follow-ups...")

        # Get all candidates in CONTACTED status
        all_candidates = []
        for worksheet in self.sheets.spreadsheet.worksheets():
            if worksheet.title == "Sheet1":
                continue
            candidates = self.sheets.get_all_applicants(worksheet.title)
            all_candidates.extend(candidates)

        followups_sent = 0
        cutoff_time = datetime.now() - timedelta(hours=self.config.follow_up_after_hours)

        for candidate in all_candidates:
            if candidate.get("status") != "CONTACTED":
                continue

            # Check if enough time has passed
            last_contact_str = candidate.get("last_contact", "")
            if not last_contact_str:
                continue

            try:
                last_contact = datetime.strptime(last_contact_str, "%Y-%m-%d %H:%M:%S")
                if last_contact > cutoff_time:
                    continue  # Not ready for follow-up yet

                # Generate follow-up message
                message = self._generate_followup(candidate)

                if dry_run:
                    logger.info(
                        f"[DRY RUN] Would send follow-up to {candidate.get('applicant_name')}"
                    )
                    logger.info(f"Message: {message}")
                    followups_sent += 1
                else:
                    room_id = candidate.get("proposal_id")
                    if not room_id:
                        continue

                    success = self.upwork.send_message(room_id, message)

                    if success:
                        self.sheets.update_status(
                            job_title=candidate.get("job_title"),
                            proposal_id=candidate.get("proposal_id"),
                            status="CONTACTED",
                            notes="Sent follow-up (auto)",
                        )
                        followups_sent += 1
                        logger.info(
                            f"Sent follow-up to {candidate.get('applicant_name')}"
                        )

            except Exception as e:
                logger.error(
                    f"Error sending follow-up to {candidate.get('applicant_name')}: {e}"
                )

        logger.info(f"Follow-ups complete: {followups_sent} messages sent")
        return followups_sent

    def batch_decline_tier3(self, dry_run: bool = False) -> int:
        """
        Send polite decline messages to Tier 3 candidates.

        Args:
            dry_run: If True, log what would be sent but don't actually send

        Returns:
            Number of decline messages sent
        """
        logger.info("Processing Tier 3 declines...")

        if not self.config.batch_decline_tier3:
            logger.info("Batch decline for Tier 3 is disabled")
            return 0

        # Get all Tier 3 candidates who haven't been rejected yet
        all_candidates = []
        for worksheet in self.sheets.spreadsheet.worksheets():
            if worksheet.title == "Sheet1":
                continue
            candidates = self.sheets.get_all_applicants(worksheet.title)
            all_candidates.extend(candidates)

        declines_sent = 0

        for candidate in all_candidates:
            if (
                candidate.get("ai_tier") != "Tier 3"
                or candidate.get("status") == "REJECTED"
            ):
                continue

            try:
                message = self._generate_decline(candidate)

                if dry_run:
                    logger.info(
                        f"[DRY RUN] Would decline {candidate.get('applicant_name')}"
                    )
                    logger.info(f"Message: {message}")
                    declines_sent += 1
                else:
                    room_id = candidate.get("proposal_id")
                    if not room_id:
                        continue

                    success = self.upwork.send_message(room_id, message)

                    if success:
                        self.sheets.update_status(
                            job_title=candidate.get("job_title"),
                            proposal_id=candidate.get("proposal_id"),
                            status="REJECTED",
                            notes="Sent polite decline (auto)",
                        )
                        declines_sent += 1
                        logger.info(f"Sent decline to {candidate.get('applicant_name')}")

            except Exception as e:
                logger.error(
                    f"Error declining {candidate.get('applicant_name')}: {e}"
                )

        logger.info(f"Declines complete: {declines_sent} messages sent")
        return declines_sent

    def _generate_initial_outreach(self, candidate: Dict[str, Any]) -> str:
        """Generate personalized initial outreach message using AI."""
        try:
            # Try to load template
            template = self.config_loader.load_message_template("initial_outreach")
        except FileNotFoundError:
            # Use default template
            template = """Hi {name}, thanks for your proposal on {job_title}. Your experience with {skills} caught my attention. I'd like to schedule a quick call to discuss the project. Here's my calendar: {calendly_link}. Looking forward to connecting!"""

        # Use AI to personalize
        prompt = f"""Generate a personalized, friendly initial outreach message for this Upwork applicant.

Template to customize:
{template}

Applicant details:
- Name: {candidate.get('applicant_name', 'there')}
- Job: {candidate.get('job_title')}
- Skills: {candidate.get('skills', 'your skills')}
- Cover letter excerpt: {candidate.get('cover_letter', '')[:200]}
- Why they're a good fit: {candidate.get('ai_reasoning', '')}

Your calendar link: {self.config.calendly_link}

Keep it:
- Under 150 words
- Professional but friendly
- Specific to their experience
- Include the calendar link

Return only the message text, no preamble."""

        try:
            response = self.ai_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()

        except Exception as e:
            logger.warning(f"AI message generation failed, using template: {e}")
            # Fallback to simple template substitution
            return template.format(
                name=candidate.get("applicant_name", "there"),
                job_title=candidate.get("job_title", "this role"),
                skills=candidate.get("skills", "your experience"),
                calendly_link=self.config.calendly_link or "[scheduling link]",
            )

    def _generate_followup(self, candidate: Dict[str, Any]) -> str:
        """Generate follow-up message."""
        try:
            template = self.config_loader.load_message_template("follow_up")
        except FileNotFoundError:
            template = """Hi {name}, following up on my previous message. Are you still interested in the {job_title} role? Let me know if the scheduling link works for you or if you'd prefer a different time."""

        return template.format(
            name=candidate.get("applicant_name", "there"),
            job_title=candidate.get("job_title", "role"),
        )

    def _generate_decline(self, candidate: Dict[str, Any]) -> str:
        """Generate polite decline message."""
        try:
            template = self.config_loader.load_message_template("decline")
        except FileNotFoundError:
            template = """Hi {name}, thank you for your interest in {job_title}. After reviewing all applications, we've decided to move forward with other candidates whose experience more closely matches our current needs. Best of luck with your future projects!"""

        return template.format(
            name=candidate.get("applicant_name", "there"),
            job_title=candidate.get("job_title", "this position"),
        )
