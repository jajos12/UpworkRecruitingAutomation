"""Data extraction and processing pipeline orchestrator."""

from typing import List, Dict, Any
from datetime import datetime

from src.upwork_client import UpworkClient
from src.ai_analyzer import AIAnalyzer
from src.sheets_manager import SheetsManager
from src.communicator import Communicator
from src.utils.logger import get_logger
from src.utils.config_loader import ConfigLoader, JobCriteria

logger = get_logger(__name__)


class Pipeline:
    """
    Orchestrates the complete hiring automation pipeline.

    Phases:
    1. Extract data from Upwork (jobs, proposals, profiles)
    2. Store in Google Sheets
    3. Analyze with AI
    4. Update sheets with scores
    5. Send automated messages
    """

    def __init__(
        self,
        upwork_client: UpworkClient,
        ai_analyzer: AIAnalyzer,
        sheets_manager: SheetsManager,
        communicator: Communicator,
        config_loader: ConfigLoader,
    ):
        """
        Initialize pipeline.

        Args:
            upwork_client: Upwork API client
            ai_analyzer: AI analyzer
            sheets_manager: Google Sheets manager
            communicator: Communication manager
            config_loader: Configuration loader
        """
        self.upwork = upwork_client
        self.ai = ai_analyzer
        self.sheets = sheets_manager
        self.communicator = communicator
        self.config_loader = config_loader
        logger.info("Pipeline initialized")

    def run_full_pipeline(
        self, fetch: bool = True, analyze: bool = True, communicate: bool = True, dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline.

        Args:
            fetch: Whether to fetch new data from Upwork
            analyze: Whether to analyze applicants with AI
            communicate: Whether to send automated messages
            dry_run: If True, don't actually send messages

        Returns:
            Dictionary with pipeline statistics
        """
        logger.info("=" * 80)
        logger.info("STARTING FULL PIPELINE")
        logger.info("=" * 80)

        stats = {
            "start_time": datetime.now(),
            "jobs_processed": 0,
            "proposals_fetched": 0,
            "applicants_analyzed": 0,
            "tier1_count": 0,
            "tier2_count": 0,
            "tier3_count": 0,
            "messages_sent": 0,
            "errors": [],
        }

        try:
            # Phase 1: Extract data
            if fetch:
                logger.info("\n--- PHASE 1: DATA EXTRACTION ---")
                extraction_stats = self._extract_data()
                stats["jobs_processed"] = extraction_stats["jobs_processed"]
                stats["proposals_fetched"] = extraction_stats["proposals_fetched"]

            # Phase 2: AI Analysis
            if analyze:
                logger.info("\n--- PHASE 2: AI ANALYSIS ---")
                analysis_stats = self._analyze_applicants()
                stats["applicants_analyzed"] = analysis_stats["analyzed"]
                stats["tier1_count"] = analysis_stats["tier1"]
                stats["tier2_count"] = analysis_stats["tier2"]
                stats["tier3_count"] = analysis_stats["tier3"]

            # Phase 3: Communication
            if communicate:
                logger.info("\n--- PHASE 3: AUTOMATED COMMUNICATION ---")
                comm_stats = self._send_communications(dry_run)
                stats["messages_sent"] = comm_stats["messages_sent"]

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            stats["errors"].append(str(e))

        stats["end_time"] = datetime.now()
        stats["duration_seconds"] = (
            stats["end_time"] - stats["start_time"]
        ).total_seconds()

        self._print_summary(stats)
        return stats

    def _extract_data(self) -> Dict[str, int]:
        """
        Extract data from Upwork and store in Google Sheets.

        Returns:
            Statistics dictionary
        """
        logger.info("Fetching open jobs...")

        try:
            jobs = self.upwork.get_open_jobs()
            logger.info(f"Found {len(jobs)} open jobs")

            total_proposals = 0

            for job in jobs:
                job_id = job["id"]
                job_title = job["title"]
                job_description = job.get("description", "")

                logger.info(f"\nProcessing job: {job_title}")

                # Get proposals for this job
                proposals = self.upwork.get_job_proposals(job_id)
                logger.info(f"Found {len(proposals)} proposals")

                # Transform proposals to applicant format
                applicants = []
                for proposal in proposals:
                    applicant = self._transform_proposal_to_applicant(
                        proposal, job_id, job_title, job_description
                    )
                    applicants.append(applicant)

                # Bulk upsert to sheets
                if applicants:
                    self.sheets.bulk_upsert_applicants(applicants)
                    total_proposals += len(applicants)

            return {
                "jobs_processed": len(jobs),
                "proposals_fetched": total_proposals,
            }

        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
            raise

    def _analyze_applicants(self) -> Dict[str, int]:
        """
        Analyze all applicants without AI scores.

        Returns:
            Statistics dictionary
        """
        logger.info("Analyzing applicants...")

        # Load all job criteria
        all_criteria = self.config_loader.load_all_job_criteria()

        if not all_criteria:
            logger.warning("No job criteria files found, skipping analysis")
            return {"analyzed": 0, "tier1": 0, "tier2": 0, "tier3": 0}

        total_analyzed = 0
        tier_counts = {"Tier 1": 0, "Tier 2": 0, "Tier 3": 0}

        for criteria in all_criteria:
            logger.info(f"\nAnalyzing applicants for: {criteria.job_title}")

            # Get all applicants for this job
            applicants = self.sheets.get_all_applicants(criteria.job_title)

            # Filter out already analyzed (unless score is 0)
            to_analyze = [
                a for a in applicants
                if not a.get("ai_score") or a.get("ai_score") == "0"
            ]

            if not to_analyze:
                logger.info("No new applicants to analyze")
                continue

            logger.info(f"Analyzing {len(to_analyze)} new applicants...")

            # For each applicant, we need to reconstruct the proposal format
            for applicant_data in to_analyze:
                try:
                    # Reconstruct proposal-like structure for AI analyzer
                    proposal = self._reconstruct_proposal_from_sheet(applicant_data)

                    # Analyze
                    evaluation = self.ai.evaluate_applicant(
                        proposal,
                        criteria,
                        applicant_data.get("job_description", ""),
                    )

                    # Update sheets
                    self.sheets.update_ai_score(
                        job_title=criteria.job_title,
                        proposal_id=applicant_data["proposal_id"],
                        score=evaluation["final_score"],
                        tier=evaluation["tier"],
                        reasoning=evaluation["reasoning"],
                        recommendation=evaluation["recommendation"],
                    )

                    total_analyzed += 1
                    tier_counts[evaluation["tier"]] += 1

                except Exception as e:
                    logger.error(
                        f"Failed to analyze {applicant_data.get('applicant_name')}: {e}"
                    )

        return {
            "analyzed": total_analyzed,
            "tier1": tier_counts["Tier 1"],
            "tier2": tier_counts["Tier 2"],
            "tier3": tier_counts["Tier 3"],
        }

    def _send_communications(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Send automated communications.

        Args:
            dry_run: If True, don't actually send messages

        Returns:
            Statistics dictionary
        """
        total_sent = 0

        # 1. Send to Tier 1 candidates
        logger.info("\nSending initial outreach to Tier 1 candidates...")
        tier1_sent = self.communicator.process_tier1_candidates(dry_run=dry_run)
        total_sent += tier1_sent

        # 2. Send follow-ups
        logger.info("\nProcessing follow-ups...")
        followups_sent = self.communicator.process_followups(dry_run=dry_run)
        total_sent += followups_sent

        # 3. Send declines to Tier 3
        logger.info("\nSending declines to Tier 3 candidates...")
        declines_sent = self.communicator.batch_decline_tier3(dry_run=dry_run)
        total_sent += declines_sent

        return {"messages_sent": total_sent}

    def _transform_proposal_to_applicant(
        self, proposal: Dict[str, Any], job_id: str, job_title: str, job_description: str
    ) -> Dict[str, Any]:
        """Transform proposal data to applicant format for sheets."""
        freelancer = proposal.get("freelancer", {})
        stats = freelancer.get("stats", {})
        location = freelancer.get("location", {})

        # Format skills
        skills = freelancer.get("skills", [])
        skills_str = ", ".join([s.get("name", "") for s in skills if isinstance(s, dict)])

        # Format work history
        work_history = freelancer.get("workHistory", {}).get("edges", [])
        work_history_summary = []
        for edge in work_history[:5]:
            node = edge.get("node", {})
            title = node.get("title", "")
            feedback = node.get("feedback", {})
            score = feedback.get("score", "N/A")
            work_history_summary.append(f"{title} ({score}/5)")
        work_history_str = "; ".join(work_history_summary) if work_history_summary else ""

        # Build profile URL
        profile_url = f"https://www.upwork.com/freelancers/{freelancer.get('id', '')}"

        return {
            "job_id": job_id,
            "job_title": job_title,
            "job_description": job_description,
            "applicant_id": freelancer.get("id", ""),
            "applicant_name": freelancer.get("name", ""),
            "profile_title": freelancer.get("title", ""),
            "proposal_id": proposal.get("id", ""),
            "hourly_rate_profile": freelancer.get("hourlyRate", ""),
            "bid_amount": proposal.get("chargedAmount", ""),
            "job_success_score": stats.get("jobSuccessScore", ""),
            "total_earnings": stats.get("totalEarnings", ""),
            "total_jobs": stats.get("totalJobsCount", ""),
            "top_rated_status": freelancer.get("topRatedStatus", ""),
            "skills": skills_str,
            "location": f"{location.get('city', '')}, {location.get('country', '')}",
            "timezone": location.get("timezone", ""),
            "cover_letter": proposal.get("coverLetter", ""),
            "screening_answers": "",  # Not in basic proposal data
            "work_history_summary": work_history_str,
            "profile_url": profile_url,
            "proposal_date": proposal.get("submittedDateTime", ""),
            "status": "NEW",
        }

    def _reconstruct_proposal_from_sheet(self, applicant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reconstruct proposal format from sheet data for AI analysis."""
        # Parse skills back to list
        skills_str = applicant_data.get("skills", "")
        skills = [{"name": s.strip()} for s in skills_str.split(",") if s.strip()]

        return {
            "id": applicant_data.get("proposal_id", ""),
            "coverLetter": applicant_data.get("cover_letter", ""),
            "chargedAmount": applicant_data.get("bid_amount", ""),
            "submittedDateTime": applicant_data.get("proposal_date", ""),
            "freelancer": {
                "id": applicant_data.get("applicant_id", ""),
                "name": applicant_data.get("applicant_name", ""),
                "title": applicant_data.get("profile_title", ""),
                "hourlyRate": applicant_data.get("hourly_rate_profile", ""),
                "location": {
                    "city": applicant_data.get("location", "").split(",")[0].strip() if applicant_data.get("location") else "",
                    "country": applicant_data.get("location", "").split(",")[-1].strip() if applicant_data.get("location") else "",
                    "timezone": applicant_data.get("timezone", ""),
                },
                "stats": {
                    "jobSuccessScore": applicant_data.get("job_success_score", ""),
                    "totalEarnings": applicant_data.get("total_earnings", ""),
                    "totalJobsCount": applicant_data.get("total_jobs", ""),
                },
                "topRatedStatus": applicant_data.get("top_rated_status", ""),
                "skills": skills,
                "workHistory": {
                    "edges": []  # Simplified
                },
            },
        }

    def _print_summary(self, stats: Dict[str, Any]) -> None:
        """Print pipeline execution summary."""
        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Duration: {stats['duration_seconds']:.1f} seconds")
        logger.info(f"Jobs processed: {stats['jobs_processed']}")
        logger.info(f"Proposals fetched: {stats['proposals_fetched']}")
        logger.info(f"Applicants analyzed: {stats['applicants_analyzed']}")
        logger.info(f"  - Tier 1 (Auto-advance): {stats['tier1_count']}")
        logger.info(f"  - Tier 2 (Review): {stats['tier2_count']}")
        logger.info(f"  - Tier 3 (Reject): {stats['tier3_count']}")
        logger.info(f"Messages sent: {stats['messages_sent']}")

        if stats["errors"]:
            logger.error(f"Errors encountered: {len(stats['errors'])}")
            for error in stats["errors"]:
                logger.error(f"  - {error}")

        logger.info("=" * 80)
