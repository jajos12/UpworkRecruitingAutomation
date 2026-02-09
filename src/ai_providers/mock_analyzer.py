"""Mock AI Analyzer for testing and development without API costs."""

import random
import re
from typing import Dict, Any, List
from src.ai_providers.base_analyzer import BaseAIAnalyzer
from src.utils.logger import get_logger

logger = get_logger(__name__)

class MockAIAnalyzer(BaseAIAnalyzer):
    """
    Mock AI analyzer for testing without API costs.
    Generates consistent random scores based on applicant name.
    """
    
    def __init__(self):
        logger.info("Initialized Mock AI Analyzer")
    
    def evaluate_applicant(
        self,
        applicant_data: Dict[str, Any],
        criteria: Any,
        job_description: str
    ) -> Dict[str, Any]:
        """Generate a mock evaluation."""
        
        name = applicant_data.get("applicant_name", "Unknown Applicant")
        logger.info(f"Generating mock evaluation for {name}")
        
        # Deterministic-ish random based on name hash to keep it consistent for same user
        # We use a simple hash of the name to seed the random number generator
        seed_value = sum(ord(c) for c in name)
        random.seed(seed_value)
        
        score = random.randint(40, 98)
        
        tier = 3
        if score >= 85:
            tier = 1
        elif score >= 65:
            tier = 2
        
        # Generate some mock reasoning
        reasons = [
            f"Candidate shows strong alignment with {job_description[:20]}...",
            "Experience seems relevant but lacks specific details on recent projects.",
            "Strong communication skills evident in the cover letter.",
            "Technical skills match the requirements well.",
            "Salary expectations are within budget."
        ]
        
        # Pick 2-3 reasons
        selected_reasons = random.sample(reasons, k=random.randint(2, 3))
        
        return {
            "score": score,
            "tier": tier,
            "reasoning": " [MOCK ANALYSIS] " + " ".join(selected_reasons),
            "recommendation": "Interview" if tier == 1 else "Review" if tier == 2 else "Reject",
            "red_flags": ["Mock red flag: Generic cover letter"] if score < 60 else [],
            "strengths": ["Mock strength: Quick learner", "Mock strength: Good availability"]
        }

    def evaluate_batch(
        self,
        applicants: List[Dict[str, Any]],
        criteria: Any,
        job_description: str
    ) -> List[Dict[str, Any]]:
        """Evaluate multiple applicants."""
        return [
            self.evaluate_applicant(applicant, criteria, job_description)
            for applicant in applicants
        ]

    def generate_criteria(self, job_description: str) -> Dict[str, Any]:
        """Generate mock criteria."""
        return {
            "must_have": ["Must have relevant experience", "Must be available immediately"],
            "nice_to_have": [
                {"description": "Previous startup experience", "importance": "high"},
                {"description": "Familiarity with remote work", "importance": "medium"}
            ],
            "red_flags": ["Poor communication", "Incomplete profile"]
        }

    def generate_interview_questions(
        self,
        applicant_data: Dict[str, Any],
        job_description: str,
        config: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Generate mock interview questions."""
        name = applicant_data.get("applicant_name", "Candidate")
        return [
            {
                "type": "Behavioral",
                "question": f"Can you tell me about the most challenging project you listed in your portfolio, specifically regarding {job_description[:10]}?",
                "context": "Looking for ability to handle pressure and technical depth.",
                "expected_answer": None
            },
            {
                "type": "Technical",
                "question": "How would you handle a race condition in a Python async application?",
                "context": "Critical for our backend architecture.",
                "expected_answer": "Should mention asyncio.Lock or similar synchronization primitives."
            },
            {
                "type": "Red Flag",
                "question": "I noticed a gap in your timeline between 2022 and 2023. Can you walk me through that period?",
                "context": "Check if they were working on undeclared side projects or just taking a break.",
                "expected_answer": None
            }
        ]

    def parse_raw_applicants(
        self,
        raw_text: str,
        job_context: str = None,
        format_hint: str = None
    ) -> Dict[str, Any]:
        """Generate mock parsed applicants from raw text."""
        logger.info("Mock parsing raw applicant data...")

        # Simple heuristic: split by double newlines or "---" to guess applicant count
        sections = re.split(r'\n{3,}|---+|\n={3,}', raw_text.strip())
        sections = [s.strip() for s in sections if len(s.strip()) > 20]

        if not sections:
            sections = [raw_text]

        applicants = []
        for i, section in enumerate(sections):
            # Try to extract a name from the first line
            lines = section.strip().split('\n')
            name = lines[0].strip().rstrip(':').strip('# ').strip('*')
            if len(name) > 60 or len(name) < 2:
                name = f"Unknown Applicant #{i + 1}"

            slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

            applicants.append({
                "freelancer_id": f"import-{slug}-{i + 1}",
                "name": name,
                "title": "Freelancer",
                "hourly_rate": round(random.uniform(20, 80), 2),
                "job_success_score": random.randint(70, 99),
                "total_earnings": round(random.uniform(5000, 100000), 2),
                "top_rated_status": random.choice([None, "Top Rated", "Top Rated Plus"]),
                "skills": ["Python", "JavaScript", "React"],
                "bio": section[:200] if len(section) > 20 else "No bio extracted",
                "certifications": [],
                "portfolio_items": [],
                "work_history_summary": None,
                "profile_url": None,
                "cover_letter": section if len(section) > 50 else "",
                "bid_amount": round(random.uniform(500, 5000), 2),
                "estimated_duration": "1-2 weeks",
                "screening_answers": None,
                "confidence": 0.6,
                "parse_notes": ["[MOCK] Data generated from text heuristics, not AI-parsed"]
            })

        return {
            "applicants": applicants,
            "warnings": ["[MOCK MODE] Using mock parser - data is auto-generated, not AI-extracted"]
        }

    def chat_with_candidate(
        self,
        query: str,
        applicant_data: Dict[str, Any],
        job_description: str,
        chat_history: List[Dict[str, Any]]
    ) -> str:
        """Mock chat response."""
        if "python" in query.lower():
            return "Yes, the candidate mentions extensive Python experience in their bio, specifically with Django and FastAPI."
        if "aws" in query.lower():
            return "The profile does not explicitly mention AWS, but they list 'Cloud Deployment' as a skill."
        return "Based on the profile, I can see they are a strong match. They have 5 years of experience and top rated status."


