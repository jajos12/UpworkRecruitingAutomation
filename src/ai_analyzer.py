"""AI-powered applicant analyzer using Claude API."""

import json
from typing import Dict, Any, Optional
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.logger import get_logger
from src.utils.config_loader import AIConfig, JobCriteria

logger = get_logger(__name__)


class AIAnalyzer:
    """
    Evaluates Upwork applicants against hiring criteria using Claude AI.

    Provides:
    - Objective scoring (0-100)
    - Tier classification (1, 2, or 3)
    - Detailed reasoning
    - Recommendations (ADVANCE, REVIEW, REJECT)
    """

    def __init__(self, config: AIConfig):
        """
        Initialize AI analyzer.

        Args:
            config: AI configuration with API key and settings
        """
        self.config = config
        self.client = Anthropic(api_key=config.api_key)
        logger.info("AI Analyzer initialized")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def evaluate_applicant(
        self, applicant: Dict[str, Any], criteria: JobCriteria, job_description: str = ""
    ) -> Dict[str, Any]:
        """
        Evaluate an applicant against job criteria.

        Args:
            applicant: Applicant data dictionary
            criteria: Job criteria
            job_description: Full job description text

        Returns:
            Dictionary with:
                - passes_must_have: bool
                - must_have_evaluation: list of criterion evaluations
                - nice_to_have_points: int (0-100)
                - nice_to_have_evaluation: list of criterion evaluations
                - red_flags_found: list of strings
                - final_score: int (0-100)
                - tier: str ("Tier 1", "Tier 2", "Tier 3")
                - reasoning: str
                - recommendation: str ("ADVANCE", "REVIEW", "REJECT")
        """
        logger.info(f"Evaluating applicant: {applicant.get('name', 'Unknown')}")

        prompt = self._build_evaluation_prompt(applicant, criteria, job_description)

        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            result = self._parse_evaluation_response(response.content[0].text)

            # Validate and classify
            result = self._classify_tier(result)

            logger.info(
                f"Evaluation complete: Score={result['final_score']}, Tier={result['tier']}"
            )
            return result

        except Exception as e:
            logger.error(f"AI evaluation failed: {e}")
            # Return default failure result
            return {
                "passes_must_have": False,
                "must_have_evaluation": [],
                "nice_to_have_points": 0,
                "nice_to_have_evaluation": [],
                "red_flags_found": ["AI evaluation failed"],
                "final_score": 0,
                "tier": "Tier 3",
                "reasoning": f"Evaluation failed: {str(e)}",
                "recommendation": "REJECT",
            }

    def _build_evaluation_prompt(
        self, applicant: Dict[str, Any], criteria: JobCriteria, job_description: str
    ) -> str:
        """Build the evaluation prompt for Claude."""
        # Extract applicant data safely
        freelancer = applicant.get("freelancer", {})
        stats = freelancer.get("stats", {})
        location = freelancer.get("location", {})

        # Format skills
        skills = freelancer.get("skills", [])
        skills_str = ", ".join([s.get("name", "") for s in skills if isinstance(s, dict)])

        # Format work history
        work_history = freelancer.get("workHistory", {}).get("edges", [])
        work_history_summary = []
        for edge in work_history[:5]:  # Top 5 jobs
            node = edge.get("node", {})
            title = node.get("title", "")
            feedback = node.get("feedback", {})
            score = feedback.get("score", "N/A")
            work_history_summary.append(f"- {title} (Rating: {score}/5)")
        work_history_str = "\n".join(work_history_summary) if work_history_summary else "No work history available"

        # Format must-have criteria
        must_have_str = "\n".join([f"- {c}" for c in criteria.must_have])

        # Format nice-to-have criteria
        nice_to_have_str = "\n".join(
            [
                f"- {c.get('criterion', '')} (+{c.get('weight', 0)} points)"
                for c in criteria.nice_to_have
            ]
        )

        # Format red flags
        red_flags_str = "\n".join([f"- {r}" for r in criteria.red_flags])

        prompt = f"""You are evaluating an Upwork job applicant. Be thorough and objective.

## Job Details
Title: {criteria.job_title}
Job ID: {criteria.job_id}

Description:
{job_description or "No description provided"}

## Hiring Criteria

### Must Have (Applicant FAILS if any of these are not met):
{must_have_str}

### Nice to Have (Add points for each):
{nice_to_have_str}

### Red Flags (Deduct points or fail):
{red_flags_str}

## Applicant Information

**Basic Info:**
- Name: {freelancer.get('name', 'N/A')}
- Profile Title: {freelancer.get('title', 'N/A')}
- Location: {location.get('city', '')}, {location.get('country', '')}
- Timezone: {location.get('timezone', 'N/A')}

**Rates & Stats:**
- Hourly Rate (Profile): ${freelancer.get('hourlyRate', 'N/A')}
- Bid Amount: ${applicant.get('chargedAmount', 'N/A')}
- Job Success Score: {stats.get('jobSuccessScore', 'N/A')}%
- Total Earnings: ${stats.get('totalEarnings', 0):,.0f}
- Total Jobs: {stats.get('totalJobsCount', 0)}
- Top Rated Status: {freelancer.get('topRatedStatus', 'None')}

**Skills:**
{skills_str or "No skills listed"}

**Work History Summary:**
{work_history_str}

**Cover Letter:**
{applicant.get('coverLetter', 'No cover letter provided')}

**Proposal Date:**
{applicant.get('submittedDateTime', 'N/A')}

## Your Task

1. **Evaluate each "Must Have" criterion.** If ANY fail, the applicant fails overall.
2. **For passing applicants, calculate points from "Nice to Have" criteria.** Award points based on how well they meet each criterion.
3. **Check for red flags** and note any concerns.
4. **Provide a final score from 0-100.**
5. **Write clear reasoning** for your evaluation (2-3 sentences).

## Response Format

Respond with ONLY valid JSON in this exact format:

{{
  "passes_must_have": true or false,
  "must_have_evaluation": [
    {{"criterion": "criterion text", "met": true or false, "evidence": "specific evidence from profile/cover letter"}}
  ],
  "nice_to_have_points": 0-100,
  "nice_to_have_evaluation": [
    {{"criterion": "criterion text", "points": 0-20, "evidence": "why points awarded or not"}}
  ],
  "red_flags_found": ["flag1", "flag2"] or [],
  "final_score": 0-100,
  "reasoning": "2-3 sentence summary explaining the score",
  "recommendation": "ADVANCE" or "REVIEW" or "REJECT"
}}

Be honest and critical. Only give high scores to truly qualified candidates.
"""
        return prompt

    def _parse_evaluation_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's JSON response."""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")

            json_str = response_text[start_idx:end_idx]
            result = json.loads(json_str)

            # Validate required fields
            required_fields = [
                "passes_must_have",
                "final_score",
                "reasoning",
                "recommendation",
            ]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            return result

        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise

    def _classify_tier(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify applicant into tier based on score.

        Tier 1: Score >= tier1_threshold (default 85) → Auto-advance
        Tier 2: Score >= tier2_threshold (default 70) → Review
        Tier 3: Score < tier2_threshold → Reject
        """
        score = evaluation["final_score"]

        if score >= self.config.tier1_threshold:
            evaluation["tier"] = "Tier 1"
            if evaluation["passes_must_have"]:
                evaluation["recommendation"] = "ADVANCE"
        elif score >= self.config.tier2_threshold:
            evaluation["tier"] = "Tier 2"
            evaluation["recommendation"] = "REVIEW"
        else:
            evaluation["tier"] = "Tier 3"
            evaluation["recommendation"] = "REJECT"

        # Override recommendation if fails must-have
        if not evaluation.get("passes_must_have", False):
            evaluation["tier"] = "Tier 3"
            evaluation["recommendation"] = "REJECT"

        return evaluation

    def batch_evaluate(
        self, applicants: list[Dict[str, Any]], criteria: JobCriteria, job_description: str = ""
    ) -> list[Dict[str, Any]]:
        """
        Evaluate multiple applicants in batch.

        Args:
            applicants: List of applicant dictionaries
            criteria: Job criteria
            job_description: Job description

        Returns:
            List of evaluation results
        """
        logger.info(f"Batch evaluating {len(applicants)} applicants...")

        results = []
        for i, applicant in enumerate(applicants, 1):
            logger.info(f"Evaluating applicant {i}/{len(applicants)}...")
            try:
                result = self.evaluate_applicant(applicant, criteria, job_description)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to evaluate applicant {i}: {e}")
                results.append({
                    "passes_must_have": False,
                    "final_score": 0,
                    "tier": "Tier 3",
                    "reasoning": f"Evaluation error: {str(e)}",
                    "recommendation": "REJECT",
                    "red_flags_found": ["Evaluation failed"],
                })

        logger.info(f"Batch evaluation complete: {len(results)} results")
        return results
