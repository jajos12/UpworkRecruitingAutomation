"""Google Gemini AI analyzer implementation."""

import json
from typing import Dict, List, Any
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from src.ai_providers.base_analyzer import BaseAIAnalyzer
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiAnalyzer(BaseAIAnalyzer):
    """
    AI analyzer using Google's Gemini models.
    
    Supports Gemini Pro and Gemini Pro Vision.
    """
    
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        """
        Initialize Gemini analyzer.
        
        Args:
            api_key: Google API key
            model: Model to use (gemini-pro, gemini-pro-vision)
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model
        logger.info(f"Gemini analyzer initialized with model: {model}")
    
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
        """Evaluate applicant using Gemini."""
        logger.info(f"Evaluating applicant: {applicant_data.get('applicant_name', 'Unknown')}")
        
        # Build the evaluation prompt
        prompt = self._build_prompt(applicant_data, criteria, job_description)
        
        try:
            # Call Gemini API
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.3,
                    'top_p': 0.8,
                    'top_k': 40,
                    'max_output_tokens': 2048,
                }
            )
            
            # Parse response
            result_text = response.text
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
            logger.error(f"Gemini evaluation failed: {e}")
            raise
    
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
        """Build the evaluation prompt for Gemini."""
        
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
4. Calculate score (0-100) based on:
   - Must-haves: Pass/fail (if any fail, max score is 60)
   - Nice-to-haves: Weight-based scoring
   - Red flags: Deduct points
   - Profile/Proposal alignment and overall professionalism
5. Identify specific strengths and red flags
6. Provide a clear recommendation

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
        """Extract and parse JSON from Gemini's response."""
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
            logger.error(f"Failed to parse Gemini response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise
