"""OpenAI-based AI analyzer implementation."""

import json
from typing import Dict, List, Any
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.ai_providers.base_analyzer import BaseAIAnalyzer
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIAnalyzer(BaseAIAnalyzer):
    """
    AI analyzer using OpenAI's GPT models.
    
    Supports GPT-5, GPT-4, GPT-4-Turbo, GPT-4o, and GPT-3.5-Turbo.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-5"):
        """
        Initialize OpenAI analyzer.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-4o-mini, gpt-4-turbo-preview, gpt-4, gpt-3.5-turbo)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        logger.info(f"OpenAI analyzer initialized with model: {model}")
    
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
        """Evaluate applicant using OpenAI."""
        logger.info(f"Evaluating applicant: {applicant_data.get('applicant_name', 'Unknown')}")
        
        # Build the evaluation prompt
        prompt = self._build_prompt(applicant_data, criteria, job_description)
        
        try:
            # Prepare API parameters
            params = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "response_format": {"type": "json_object"}
            }

            # Reasoning models (o1, o3) have specific restrictions
            is_reasoning_model = self.model.startswith(('o1', 'o3'))
            
            if not is_reasoning_model:
                # Add system message for non-reasoning models
                params["messages"].insert(0, {
                    "role": "system",
                    "content": "You are an expert technical recruiter analyzing job applicants. Provide detailed, objective evaluations based on the criteria provided."
                })
                # # Add temperature for non-reasoning models
                # params["temperature"] = 0.3
            else:
                # o1-preview and o1-mini don't support JSON mode yet in some versions, 
                # but they are very good at following instructions.
                # If they support it, we keep it, otherwise we might need to remove it.
                # For now, let's just fix the temperature issue.
                logger.info(f"Using reasoning model '{self.model}' - omitting temperature")

            # Call OpenAI
            response = self.client.chat.completions.create(**params)
            
            # Parse response
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
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
            logger.error(f"OpenAI evaluation failed: {e}")
            raise
    
    def evaluate_batch(
        self,
        applicants: List[Dict[str, Any]],
        criteria: Any,
        job_description: str
    ) -> List[Dict[str, Any]]:
        """Evaluate multiple applicants (sequential for now)."""
        results = []
        for applicant in applicants:
            try:
                result = self.evaluate_applicant(applicant, criteria, job_description)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to evaluate applicant: {e}")
                # Return a default low-score evaluation
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
        """Build the evaluation prompt."""
        
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
