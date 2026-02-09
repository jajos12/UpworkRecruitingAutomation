"""OpenAI-based AI analyzer implementation."""

import json
from typing import Dict, List, Any, Optional
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

    def generate_criteria(self, job_description: str) -> Dict[str, Any]:
        """Generate criteria using OpenAI."""
        logger.info("Generating criteria from job description...")
        
        prompt = f"""
        You are an expert technical recruiter. Analyze the following job description and extract key hiring criteria.
        
        JOB DESCRIPTION:
        {job_description}
        
        Return a JSON object with this exact structure:
        {{
            "must_have": ["list of 3-7 absolute hard requirements"],
            "nice_to_have": [
                {{"text": "requirement description", "weight": "High/Medium/Low"}}
            ],
            "red_flags": ["list of 3-5 warning signs or negative indicators mentioned or implied"]
        }}
        """
        
        try:
            params = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant that extracts structured data from text."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "response_format": {"type": "json_object"}
            }

            # Handle reasoning/o1 models logic if present
            if self.model.startswith(('o1', 'o3')):
                params["messages"].pop(0) # Remove system prompt
            
            response = self.client.chat.completions.create(**params)
            
            result_text = response.choices[0].message.content
            return json.loads(result_text)
            
        except Exception as e:
            logger.error(f"OpenAI criteria generation failed: {e}")
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

    def evaluate_batch(
        self,
        applicants: List[Dict[str, Any]],
        criteria: Any,
        job_description: str
    ) -> List[Dict[str, Any]]:
        """Evaluate multiple applicants using sequential processing."""
        # Note: OpenAI supports batch API but for simplicity in this version we run sequentially
        # In a production scaled version, we would implement async batching here
        results = []
        for applicant in applicants:
            try:
                result = self.evaluate_applicant(applicant, criteria, job_description)
                results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating applicant in batch: {e}")
                results.append({"error": str(e)})
        return results

    def generate_criteria(self, job_description: str) -> Dict[str, Any]:
        """Generate criteria from JD (Placeholder if not already implemented)."""
        # Note: This is a fallback if the file didn't already have it.
        # Ideally this should use the same logic as evaluate_applicant but different prompt.
        # For brevity in this fix, creating a simple version.
        
        prompt = f"""
        Analyze the following job description and extract key hiring criteria.
        Job Description:
        {job_description}
        
        Return JSON format:
        {{
            "must_have": ["list of hard requirements"],
            "nice_to_have": [{{ "criterion": "preference", "weight": "high/medium/low" }}],
            "red_flags": ["list of negative signals to watch for"]
        }}
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)

    def generate_interview_questions(
        self,
        applicant_data: Dict[str, Any],
        job_description: str,
        config: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Generate specific interview questions."""
        
        # Default configuration
        if not config:
            config = {
                "behavioral_count": 1,
                "technical_count": 2,
                "red_flag_count": 1,
                "soft_skill_count": 0,
                "custom_focus": None
            }

        total_questions = (
            config.get("behavioral_count", 0) + 
            config.get("technical_count", 0) + 
            config.get("red_flag_count", 0) +
            config.get("soft_skill_count", 0)
        )
        if total_questions == 0:
            total_questions = 5

        applicant_summary = f"""
        Name: {applicant_data.get('applicant_name')}
        Title: {applicant_data.get('profile_title')}
        Skills: {', '.join(applicant_data.get('skills', []))}
        Overview: {applicant_data.get('bio')}
        Cover Letter: {applicant_data.get('cover_letter')}
        """
        
        focus_prompt = ""
        if config.get("custom_focus"):
            focus_prompt = f"Additional focus: Please specifically ask about {config['custom_focus']}."

        prompt = f"""
        You are an expert technical recruiter preparing an interview guide.
        
        JOB DESCRIPTION:
        {job_description[:1500]}...
        
        CANDIDATE PROFILE:
        {applicant_summary}
        
        Generate {total_questions} high-quality, personalized interview questions to vet this specific candidate against the job.
        
        Configuration Requirements:
        - Behavioral Questions: {config.get('behavioral_count', 1)}
        - Technical Questions: {config.get('technical_count', 2)}
        - Red Flag/Gap Analysis: {config.get('red_flag_count', 1)}
        - Soft Skill/Culture: {config.get('soft_skill_count', 0)}
        {focus_prompt}
        
        Rules:
        1. "Context" should explain to the interviewer why they are asking this.
        2. "Expected Answer" should give brief bullet points of what a good answer looks like.
        
        Return a JSON object with this exact structure:
        {{
          "questions": [
            {{
                "type": "Behavioral" | "Technical" | "Red Flag" | "Soft Skill",
                "question": "The question text",
                "context": "Why ask this / what to look for",
                "expected_answer": "Key points to listen for"
            }}
          ]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            if isinstance(data, dict) and "questions" in data:
                return data["questions"]
            elif isinstance(data, list):
                return data
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error generating interview questions: {e}")
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
        """Parse raw text into structured applicant data using OpenAI."""
        logger.info("Parsing raw applicant data with OpenAI...")

        prompt = self._build_parse_prompt(raw_text, job_context, format_hint)

        try:
            params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert data parser that extracts structured applicant data from raw text. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}
            }

            if self.model.startswith(('o1', 'o3')):
                params["messages"].pop(0)

            response = self.client.chat.completions.create(**params)
            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            logger.info(f"Parsed {len(result.get('applicants', []))} applicants from raw text")
            return result

        except Exception as e:
            logger.error(f"OpenAI parsing failed: {e}")
            return {"applicants": [], "warnings": [f"Parsing failed: {str(e)}"]}

    def _build_parse_prompt(
        self,
        raw_text: str,
        job_context: Optional[str] = None,
        format_hint: Optional[str] = None
    ) -> str:
        """Build the prompt for parsing raw applicant text."""
        return f"""Parse the following raw text into structured applicant profiles.

The text may contain data for ONE or MULTIPLE applicants in any format (CSV, markdown, plain text, JSON, etc).

{f'FORMAT HINT: The input appears to be in {format_hint} format.' if format_hint else ''}
{f'JOB CONTEXT: This data is for the following job posting:\\n{job_context[:500]}' if job_context else ''}

For EACH applicant, extract these fields (use null if not found):
- name (required), title, hourly_rate (USD), job_success_score (0-100), total_earnings (USD)
- top_rated_status ("Top Rated Plus"/"Top Rated"/null), skills (array), bio, certifications (array)
- portfolio_items (array of {{title, desc}}), work_history_summary, profile_url
- cover_letter, bid_amount (number), estimated_duration, screening_answers

Generate freelancer_id as "import-<name-slug>-<index>". Set confidence (0-1) and parse_notes array for each.

Return JSON: {{"applicants": [{{freelancer_id, name, title, hourly_rate, job_success_score, total_earnings, top_rated_status, skills, bio, certifications, portfolio_items, work_history_summary, profile_url, cover_letter, bid_amount, estimated_duration, screening_answers, confidence, parse_notes}}], "warnings": []}}

RAW TEXT:
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
        """Chat with the candidate's profile."""
        
        system_prompt = f"""
        You are "The Investigator", an expert technical recruiter assistant. 
        Your goal is to answer questions about a specific job applicant based *strictly* on their provided profile data.
        
        JOB CONTEXT:
        {job_description[:1000]}...
        
        CANDIDATE DATA:
        Name: {applicant_data.get('applicant_name')}
        Title: {applicant_data.get('profile_title')}
        Skills: {', '.join(applicant_data.get('skills', []))}
        Bio: {applicant_data.get('bio')}
        Cover Letter: {applicant_data.get('cover_letter')}
        Work History: {applicant_data.get('work_history_summary')}
        Certifications: {', '.join(applicant_data.get('certifications', []))}
        Portfolio: {str(applicant_data.get('portfolio_items', []))}
        
        INSTRUCTIONS:
        1. Answer the user's question accurately based on the Candidate Data.
        2. If the information is not in the profile, explicitly say "The profile does not mention..."
        3. Be critical but fair. Point out inconsistencies if asked.
        4. Keep answers concise and professional.
        """

        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add history (limit to last 10 messages to save context)
        for msg in chat_history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        # Add current query
        messages.append({"role": "user", "content": query})

        try:
             # Reasoning models (o1, o3) logic again
            if self.model.startswith(('o1', 'o3')):
                # Merge system prompt into user prompt for o1 models
                messages = [{"role": "user", "content": system_prompt + "\n\nChat History:\n" + str(chat_history[-5:]) + "\n\nQuestion: " + query}]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in chat_with_candidate: {e}")
            return "I apologized, but I encountered an error analyzing the profile for this question."

