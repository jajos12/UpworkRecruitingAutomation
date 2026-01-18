"""Google Sheets manager for storing applicant data and AI scores."""

import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.utils.logger import get_logger
from src.utils.config_loader import GoogleSheetsConfig

logger = get_logger(__name__)


class SheetsManager:
    """
    Manages Google Sheets integration for storing and updating applicant data.

    Schema:
    - job_id: Upwork job ID
    - job_title: Job posting title
    - applicant_id: Unique freelancer ID
    - applicant_name: Freelancer name
    - profile_title: Freelancer's profile headline
    - proposal_id: Unique proposal ID
    - hourly_rate_profile: Freelancer's standard hourly rate
    - bid_amount: Amount bid on this job
    - job_success_score: Percentage (0-100)
    - total_earnings: Lifetime earnings on Upwork
    - total_jobs: Number of jobs completed
    - top_rated_status: True/False
    - skills: Comma-separated list
    - location: City, Country
    - timezone: Timezone string
    - cover_letter: Full cover letter text
    - screening_answers: Answers to screening questions
    - work_history_summary: Summary of past work
    - profile_url: Link to Upwork profile
    - proposal_date: Date proposal submitted
    - ai_score: 0-100 score from AI
    - ai_tier: Tier 1, Tier 2, or Tier 3
    - ai_reasoning: AI's evaluation reasoning
    - recommendation: ADVANCE, REVIEW, or REJECT
    - status: NEW, CONTACTED, INTERVIEWING, HIRED, REJECTED
    - last_contact: Last contact date/time
    - notes: Additional notes
    """

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    HEADERS = [
        "job_id",
        "job_title",
        "applicant_id",
        "applicant_name",
        "profile_title",
        "proposal_id",
        "hourly_rate_profile",
        "bid_amount",
        "job_success_score",
        "total_earnings",
        "total_jobs",
        "top_rated_status",
        "skills",
        "location",
        "timezone",
        "cover_letter",
        "screening_answers",
        "work_history_summary",
        "profile_url",
        "proposal_date",
        "ai_score",
        "ai_tier",
        "ai_reasoning",
        "recommendation",
        "status",
        "last_contact",
        "notes",
        "last_updated",
    ]

    def __init__(self, config: GoogleSheetsConfig):
        """
        Initialize Google Sheets manager.

        Args:
            config: Google Sheets configuration
        """
        self.config = config
        logger.info("Initializing Google Sheets manager...")

        # Authenticate
        creds = Credentials.from_service_account_file(
            config.credentials_path, scopes=self.SCOPES
        )
        self.client = gspread.authorize(creds)

        # Open spreadsheet
        try:
            self.spreadsheet = self.client.open_by_key(config.spreadsheet_id)
            logger.info(f"Connected to spreadsheet: {self.spreadsheet.title}")
        except gspread.SpreadsheetNotFound:
            raise ValueError(
                f"Spreadsheet not found: {config.spreadsheet_id}. "
                "Make sure the service account email has access."
            )

    def get_or_create_worksheet(
        self, title: str, rows: int = 1000, cols: int = 30
    ) -> gspread.Worksheet:
        """
        Get existing worksheet or create new one.

        Args:
            title: Worksheet title
            rows: Number of rows for new worksheet
            cols: Number of columns for new worksheet

        Returns:
            Worksheet instance
        """
        try:
            worksheet = self.spreadsheet.worksheet(title)
            logger.debug(f"Found existing worksheet: {title}")
            return worksheet
        except gspread.WorksheetNotFound:
            logger.info(f"Creating new worksheet: {title}")
            worksheet = self.spreadsheet.add_worksheet(
                title=title, rows=rows, cols=cols
            )

            # Add headers
            worksheet.append_row(self.HEADERS)
            # Format headers (bold)
            worksheet.format("A1:AB1", {"textFormat": {"bold": True}})

            return worksheet

    def upsert_applicant(self, applicant_data: Dict[str, Any]) -> None:
        """
        Insert or update applicant record in the appropriate worksheet.

        Args:
            applicant_data: Dictionary with applicant data matching HEADERS schema
        """
        job_title = applicant_data.get("job_title", "Unknown Job")
        worksheet = self.get_or_create_worksheet(job_title)

        proposal_id = applicant_data.get("proposal_id")
        if not proposal_id:
            logger.error("proposal_id is required for upsert")
            return

        # Add timestamp
        applicant_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Find existing row by proposal_id
        try:
            cell = worksheet.find(proposal_id, in_column=6)  # proposal_id is column 6
            row_num = cell.row

            # Update existing row
            row_data = self._dict_to_row(applicant_data)
            worksheet.update(f"A{row_num}:AB{row_num}", [row_data])
            logger.info(f"Updated applicant: {applicant_data.get('applicant_name')}")

        except gspread.CellNotFound:
            # Append new row
            row_data = self._dict_to_row(applicant_data)
            worksheet.append_row(row_data)
            logger.info(f"Added new applicant: {applicant_data.get('applicant_name')}")

    def bulk_upsert_applicants(self, applicants: List[Dict[str, Any]]) -> None:
        """
        Upsert multiple applicants efficiently.

        Args:
            applicants: List of applicant data dictionaries
        """
        logger.info(f"Bulk upserting {len(applicants)} applicants...")

        # Group by job title
        by_job = {}
        for applicant in applicants:
            job_title = applicant.get("job_title", "Unknown Job")
            if job_title not in by_job:
                by_job[job_title] = []
            by_job[job_title].append(applicant)

        # Process each job's applicants
        for job_title, job_applicants in by_job.items():
            worksheet = self.get_or_create_worksheet(job_title)

            # Get all existing proposal IDs
            try:
                proposal_ids = worksheet.col_values(6)[1:]  # Skip header
            except Exception:
                proposal_ids = []

            # Separate updates and inserts
            updates = []
            inserts = []

            for applicant in job_applicants:
                applicant["last_updated"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                proposal_id = applicant.get("proposal_id")

                if proposal_id in proposal_ids:
                    row_num = proposal_ids.index(proposal_id) + 2  # +2 for header and 0-indexing
                    updates.append((row_num, self._dict_to_row(applicant)))
                else:
                    inserts.append(self._dict_to_row(applicant))

            # Batch update existing rows
            if updates:
                for row_num, row_data in updates:
                    worksheet.update(f"A{row_num}:AB{row_num}", [row_data])

            # Batch insert new rows
            if inserts:
                worksheet.append_rows(inserts)

            logger.info(
                f"Job '{job_title}': Updated {len(updates)}, Added {len(inserts)}"
            )

    def get_applicant(
        self, job_title: str, proposal_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get an applicant's data by proposal ID.

        Args:
            job_title: Job title (worksheet name)
            proposal_id: Proposal ID to search for

        Returns:
            Applicant data dictionary or None if not found
        """
        try:
            worksheet = self.spreadsheet.worksheet(job_title)
            cell = worksheet.find(proposal_id, in_column=6)
            row_data = worksheet.row_values(cell.row)

            return self._row_to_dict(row_data)

        except (gspread.WorksheetNotFound, gspread.CellNotFound):
            logger.debug(f"Applicant not found: {proposal_id}")
            return None

    def get_all_applicants(self, job_title: str) -> List[Dict[str, Any]]:
        """
        Get all applicants for a job.

        Args:
            job_title: Job title (worksheet name)

        Returns:
            List of applicant dictionaries
        """
        try:
            worksheet = self.spreadsheet.worksheet(job_title)
            all_rows = worksheet.get_all_values()

            if len(all_rows) <= 1:  # Only headers or empty
                return []

            headers = all_rows[0]
            applicants = []

            for row in all_rows[1:]:
                applicant = dict(zip(headers, row))
                applicants.append(applicant)

            return applicants

        except gspread.WorksheetNotFound:
            logger.warning(f"Worksheet not found: {job_title}")
            return []

    def update_ai_score(
        self,
        job_title: str,
        proposal_id: str,
        score: int,
        tier: str,
        reasoning: str,
        recommendation: str,
    ) -> None:
        """
        Update AI score for an applicant.

        Args:
            job_title: Job title (worksheet name)
            proposal_id: Proposal ID
            score: AI score (0-100)
            tier: Tier classification
            reasoning: AI reasoning text
            recommendation: ADVANCE, REVIEW, or REJECT
        """
        try:
            worksheet = self.spreadsheet.worksheet(job_title)
            cell = worksheet.find(proposal_id, in_column=6)
            row_num = cell.row

            # Update AI columns (U, V, W, X = 21, 22, 23, 24)
            worksheet.update(f"U{row_num}:X{row_num}", [[score, tier, reasoning, recommendation]])
            logger.info(f"Updated AI score for proposal {proposal_id}: {score}")

        except (gspread.WorksheetNotFound, gspread.CellNotFound) as e:
            logger.error(f"Failed to update AI score: {e}")

    def update_status(
        self, job_title: str, proposal_id: str, status: str, notes: str = ""
    ) -> None:
        """
        Update applicant status.

        Args:
            job_title: Job title (worksheet name)
            proposal_id: Proposal ID
            status: NEW, CONTACTED, INTERVIEWING, HIRED, REJECTED
            notes: Optional notes
        """
        try:
            worksheet = self.spreadsheet.worksheet(job_title)
            cell = worksheet.find(proposal_id, in_column=6)
            row_num = cell.row

            # Update status and notes columns (Y, Z, AA = 25, 26, 27)
            last_contact = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.update(f"Y{row_num}:AA{row_num}", [[status, last_contact, notes]])
            logger.info(f"Updated status for proposal {proposal_id}: {status}")

        except (gspread.WorksheetNotFound, gspread.CellNotFound) as e:
            logger.error(f"Failed to update status: {e}")

    def get_tier1_candidates(self) -> List[Dict[str, Any]]:
        """
        Get all Tier 1 candidates across all worksheets who haven't been contacted.

        Returns:
            List of Tier 1 candidate dictionaries
        """
        tier1_candidates = []

        for worksheet in self.spreadsheet.worksheets():
            if worksheet.title == "Sheet1":  # Skip default sheet
                continue

            all_rows = worksheet.get_all_values()
            if len(all_rows) <= 1:
                continue

            headers = all_rows[0]

            for row in all_rows[1:]:
                applicant = dict(zip(headers, row))

                # Check if Tier 1 and not yet contacted
                if (
                    applicant.get("ai_tier") == "Tier 1"
                    and applicant.get("status") in ["NEW", ""]
                ):
                    tier1_candidates.append(applicant)

        logger.info(f"Found {len(tier1_candidates)} Tier 1 candidates to contact")
        return tier1_candidates

    def _dict_to_row(self, data: Dict[str, Any]) -> List[Any]:
        """Convert dictionary to row list matching HEADERS order."""
        return [str(data.get(header, "")) for header in self.HEADERS]

    def _row_to_dict(self, row: List[Any]) -> Dict[str, Any]:
        """Convert row list to dictionary."""
        return dict(zip(self.HEADERS, row))
