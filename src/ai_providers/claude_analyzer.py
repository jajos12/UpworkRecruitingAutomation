"""Claude (Anthropic) AI analyzer implementation."""

import json
import re
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from src.ai_providers.base_analyzer import BaseAIAnalyzer
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ClaudeAnalyzer(BaseAIAnalyzer):
    """
    AI analyzer using Anthropic's Claude models.
    
    Supports Claude 4 family (Opus, Sonnet, Haiku).
    """
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4.5"):
        """
        Initialize Claude analyzer.
        
        Args:
            api_key: Anthropic API key
            model: Model to use (claude-sonnet-4, claude-opus-4, etc.)
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = 4096
        logger.info(f"Claude analyzer initialized with model: {model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def evaluate_applicant(
        self,
        applicant_data: Dict[str, Any],
        criteria: Any,
        job_description: str
    ) -> Dict[str, Any]:
        """Evaluate applicant using Claude."""
        logger.info(f"Evaluating applicant: {applicant_data.get('applicant_name', 'Unknown')}")
        
        # Build the evaluation prompt
        prompt = self._build_prompt(applicant_data, criteria, job_description)
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response
            result_text = response.content[0].text
            result = self._parse_json_response(result_text)
            
            # Ensure required fields and validate
            score = int(result.get("score", 0))
            tier = self._determine_tier(score)
            
            evaluation = {
                "score": score,
                "tier": tier,
                "reasoning": result.get("reasoning", ""),
                "recommendation": result.get("recommendation", ""),
                "red_flags": result.get("red_flags", []),
                "strengths": result.get("strengths", [])
            }
            
            logger.info(f"Evaluation complete: {applicant_data.get('applicant_name')} - Tier {tier}, Score {score}")
            return evaluation
            
        except Exception as e:
            logger.error(f"Claude evaluation failed: {e}")
            raise

    def generate_criteria(self, job_description: str) -> Dict[str, Any]:
        """Generate criteria using Claude."""
        logger.info("Generating criteria from job description...")
        
        prompt = f"""
        You are an expert technical recruiter. Analyze the following job description and extract key hiring criteria.
        
        JOB DESCRIPTION:
        {job_description}
        
        Return valid JSON with this exact structure:
        {{
            "must_have": ["list of 3-7 absolute hard requirements"],
            "nice_to_have": [
                {{"text": "requirement description", "weight": "High/Medium/Low"}}
            ],
            "red_flags": ["list of 3-5 warning signs or negative indicators mentioned or implied"]
        }}
        """
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.content[0].text
            return self._parse_json_response(result_text)
            
        except Exception as e:
            logger.error(f"Claude criteria generation failed: {e}")
            return {
                "must_have": [],
                "nice_to_have": [],
                "red_flags": []
            }
    
    def evaluate_batch(
        self,
        applicants: List[Dict[str, Any]],
        criteria: Any,
        job_description: str
    ) -> List[Dict[str, Any]]:
        """Evaluate multiple applicants (sequential)."""
        results = []
        for applicant in applicants:
            try:
                result = self.evaluate_applicant(applicant, criteria, job_description)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to evaluate applicant: {e}")
                results.append({
                    "score": 0,
                    "tier": 3,
                    "reasoning": f"Evaluation failed: {str(e)}",
                    "recommendation": "Review manually",
                    "red_flags": ["Evaluation error"],
                    "strengths": []
                })
        return results
    
    def _build_prompt(
        self,
        applicant_data: Dict[str, Any],
        criteria: Any,
        job_description: str
    ) -> str:
        """Build the evaluation prompt for Claude."""
        
        prompt = f"""Evaluate this Upwork freelancer for the following job:

JOB DESCRIPTION:
{job_description}

HIRING CRITERIA:

Must-Have Requirements (all must be met):
"""
        for req in criteria.must_have:
            prompt += f"  - {req}\n"
        
        prompt += "\nNice-to-Have (weighted preferences):\n"
        for item in criteria.nice_to_have:
            prompt += f"  - {item['criterion']} (weight: {item['weight']})\n"
        
        if criteria.red_flags:
            prompt += "\nRed Flags to watch for:\n"
            for flag in criteria.red_flags:
                prompt += f"  - {flag}\n"
        
        prompt += f"""

APPLICANT PROFILE:
Name: {applicant_data.get('applicant_name', 'N/A')}
Title: {applicant_data.get('profile_title', 'N/A')}
Hourly Rate: ${applicant_data.get('hourly_rate_profile', 'N/A')}
Job Success Score: {applicant_data.get('job_success_score', 'N/A')}%
Total Earnings: ${applicant_data.get('total_earnings', 'N/A')}
Top Rated Status: {applicant_data.get('top_rated_status', 'N/A')}

Skills: {', '.join(applicant_data.get('skills', []))}
Bio/Overview:
{applicant_data.get('bio', 'N/A')}

Certifications: {', '.join(applicant_data.get('certifications', [])) if applicant_data.get('certifications') else 'None'}

Portfolio Highlights:
{chr(10).join([f"- {item['title']}: {item['desc']}" for item in applicant_data.get('portfolio_items', [])]) if applicant_data.get('portfolio_items') else 'None listed'}

Work History: {applicant_data.get('work_history_summary', 'N/A')}

COVER LETTER:
{applicant_data.get('cover_letter', 'N/A')}

BID AMOUNT: ${applicant_data.get('bid_amount', 'N/A')}

INSTRUCTIONS:
1. Evaluate the "Storefront": Assess the freelancer's Bio, Portfolio, and Certifications. Does their profile establish them as an expert in the niche required?
2. Evaluate the "Pitch": Assess the Cover Letter. Is it personalized? Does it address the specific needs of the Job Description?
3. Alignment Check: Do the profile and proposal complement each other? A Tier 1 candidate has both a strong storefront and a tailored pitch.
4. Value Assessment (ROI): 
   - Compare the Bid Amount (${applicant_data.get('bid_amount', 'N/A')}) against the implied budget in the Job Description.
   - Compare the Bid Amount against the freelancer's Profile Rate (${applicant_data.get('hourly_rate_profile', 'N/A')}).
   - Is this freelancer providing good value? High-tier experts at professional rates are "Premium Value," while talented but cheaper freelancers are "High ROI."
5. Calculate score (0-100) based on:
   - Must-haves: Pass/fail (if any fail, max score is 60)
   - Nice-to-haves: Weight-based scoring
   - Value/ROI: Does the price make sense for the quality?
   - Red flags: Deduct points
   - Profile/Proposal alignment and overall professionalism
6. Identify specific strengths and red flags
7. Provide a clear recommendation

Return your evaluation as JSON with this exact structure:
{{
  "score": <number 0-100>,
  "reasoning": "<detailed explanation of the evaluation>",
  "recommendation": "<specific action to take>",
  "red_flags": [<list of concerning items>],
  "strengths": [<list of positive attributes>]
}}"""
        
        return prompt
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Extract and parse JSON from Claude's response."""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[start_idx:end_idx]
            result = json.loads(json_str)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse Claude response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise

    def evaluate_batch(
        self,
        applicants: List[Dict[str, Any]],
        criteria: Any,
        job_description: str
    ) -> List[Dict[str, Any]]:
        """Evaluate multiple applicants."""
        # Simple loop implementation
        return [self.evaluate_applicant(app, criteria, job_description) for app in applicants]

    def generate_criteria(self, job_description: str) -> Dict[str, Any]:
        """Generate criteria prompt for Claude."""
        # Simplified implementation to satisfy abstract base class
        prompt = f"""
        Extract hiring criteria from this job description:
        {job_description[:1000]}...
        
        Return JSON format: {{ "must_have": [], "nice_to_have": [], "red_flags": [] }}
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            text = message.content[0].text
            start = text.find('{') 
            end = text.rfind('}') + 1
            return json.loads(text[start:end]) if start >= 0 else {}
        except Exception:
            return {}

    def generate_interview_questions(
        self,
        applicant_data: Dict[str, Any],
        job_description: str,
        config: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Generate interview questions using Claude."""

        # Default config
        config = config or {}
        b_count = config.get("behavioral_count", 2)
        t_count = config.get("technical_count", 2)
        r_count = config.get("red_flag_count", 1)
        
        prompt = f"""
        You are an expert technical interviewer.
        
        JOB: {job_description[:500]}
        CANDIDATE: {applicant_data.get('applicant_name')}
        SKILLS: {applicant_data.get('skills')}
        BIO: {applicant_data.get('bio')}
        
        Create tailored interview questions:
        - {b_count} Behavioral
        - {t_count} Technical
        - {r_count} Red Flag/Gap Analysis
        
        Return purely a JSON array of objects with keys: type, question, context, expected_answer.
        """
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            text = message.content[0].text
            start = text.find('[')
            end = text.rfind(']') + 1
            
            if start >= 0 and end > start:
                return json.loads(text[start:end])
            return []
            
        except Exception as e:
            logger.error(f"Claude error generating questions: {e}")
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def parse_raw_applicants(
        self,
        raw_text: str,
        job_context: str = None,
        format_hint: str = None
    ) -> Dict[str, Any]:
        """Parse raw text into structured applicant data using Claude."""
        logger.info("Parsing raw applicant data with Claude...")

        prompt = self._build_parse_prompt(raw_text, job_context, format_hint)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text
            result = self._parse_json_response(result_text)

            logger.info(f"Parsed {len(result.get('applicants', []))} applicants from raw text")
            return result

        except Exception as e:
            logger.error(f"Claude parsing failed: {e}")
            return {"applicants": [], "warnings": [f"Parsing failed: {str(e)}"]}

    def _build_parse_prompt(
        self,
        raw_text: str,
        job_context: Optional[str] = None,
        format_hint: Optional[str] = None
    ) -> str:
        """Build the prompt for parsing raw applicant text."""
        return f"""You are an expert data parser for a recruitment platform. Parse the following raw text into structured applicant profiles.

The text may contain data for ONE or MULTIPLE applicants. It could be in any format: CSV, markdown table, plain text, copy-pasted from a website, JSON, email thread, or completely unstructured notes.

{f'FORMAT HINT: The input appears to be in {format_hint} format.' if format_hint else ''}
{f'JOB CONTEXT: This data is for the following job posting:\\n{job_context[:500]}' if job_context else ''}

For EACH applicant you can identify, extract as many of these fields as possible:
- name (string, required - use "Unknown Applicant #N" if not found)
- title (string, their professional title/headline)
- hourly_rate (number, in USD)
- job_success_score (integer, 0-100 percentage)
- total_earnings (number, in USD)
- top_rated_status (string: "Top Rated Plus", "Top Rated", or null)
- skills (array of strings)
- bio (string, their profile overview/summary)
- certifications (array of strings)
- portfolio_items (array of objects with "title" and "desc" keys)
- work_history_summary (string)
- profile_url (string, URL to their profile)
- cover_letter (string, their proposal/cover letter text)
- bid_amount (number, their proposed rate/bid for this job)
- estimated_duration (string, e.g. "2 weeks")
- screening_answers (string, answers to screening questions)

RULES:
1. If a field is not present in the text, use null (not empty string)
2. Generate a unique freelancer_id for each applicant: "import-<name-slug>-<index>" (e.g. "import-john-doe-1")
3. For skills, parse from any mention of technologies, tools, languages, or competencies
4. Set a "confidence" score (0.0 to 1.0) for each applicant based on how much data you could extract
5. Add "parse_notes" array with any warnings (e.g. "bid_amount not found, defaulting to 0")
6. If the text is clearly NOT applicant data, return empty applicants array with a warning

Return valid JSON with this exact structure:
{{
    "applicants": [
        {{
            "freelancer_id": "import-john-doe-1",
            "name": "John Doe",
            "title": "Senior Developer",
            "hourly_rate": 50.0,
            "job_success_score": 95,
            "total_earnings": 50000.0,
            "top_rated_status": "Top Rated",
            "skills": ["Python", "JavaScript"],
            "bio": "Experienced developer...",
            "certifications": [],
            "portfolio_items": [],
            "work_history_summary": "5 years of experience...",
            "profile_url": null,
            "cover_letter": "I am excited to apply...",
            "bid_amount": 2000.0,
            "estimated_duration": "2 weeks",
            "screening_answers": null,
            "confidence": 0.85,
            "parse_notes": ["hourly_rate estimated from bid"]
        }}
    ],
    "warnings": []
}}

RAW TEXT TO PARSE:
---
{raw_text}
---"""

    def chat_with_candidate(
        self,
        query: str,
        applicant_data: Dict[str, Any],
        job_description: str,
        chat_history: List[Dict[str, Any]]
    ) -> str:
        """Chat with candidate using Claude."""
        
        system_prompt = f"""
        You are "The Investigator", an expert technical recruiter assistant. 
        Answer based strictly on the provided profile.
        
        CANDIDATE: {applicant_data.get('applicant_name')}
        BIO: {applicant_data.get('bio')}
        SKILLS: {applicant_data.get('skills')}
        COVER LETTER: {applicant_data.get('cover_letter')}
        
        Keep answers concise.
        """
        
        # Build messages including history
        messages = []
        for msg in chat_history[-10:]:
             messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": query})

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system_prompt,
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude chat error: {e}")
            return "Error processing your question with Claude."

