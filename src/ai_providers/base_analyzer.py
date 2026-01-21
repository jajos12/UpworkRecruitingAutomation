"""Base abstract class for AI analyzers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any


class BaseAIAnalyzer(ABC):
    """
    Abstract base class for AI-powered applicant analyzers.
    
    All AI provider implementations must inherit from this class
    and implement the required methods.
    """
    
    @abstractmethod
    def evaluate_applicant(
        self,
        applicant_data: Dict[str, Any],
        criteria: Any,
        job_description: str
    ) -> Dict[str, Any]:
        """
        Evaluate a single applicant against job criteria.
        
        Args:
            applicant_data: Dictionary containing applicant information
            criteria: Job criteria object with must_have, nice_to_have, red_flags
            job_description: Full job description text
            
        Returns:
            Dictionary with keys:
                - score (int): 0-100
                - tier (int): 1, 2, or 3
                - reasoning (str): Explanation of the evaluation
                - recommendation (str): Action recommendation
                - red_flags (list): List of identified red flags
                - strengths (list): List of identified strengths
        """
        pass
    
    @abstractmethod
    def generate_criteria(self, job_description: str) -> Dict[str, Any]:
        """
        Generate hiring criteria from a job description.
        
        Args:
            job_description: Full job description text
            
        Returns:
            Dictionary with:
                - must_have (List[str]): Essential requirements
                - nice_to_have (List[Dict]): Preferences with expected importance
                - red_flags (List[str]): Warning signs to look for
        """
        pass
    
    @abstractmethod
    def evaluate_batch(
        self,
        applicants: List[Dict[str, Any]],
        criteria: Any,
        job_description: str
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple applicants in batch (optional optimization).
        
        Args:
            applicants: List of applicant data dictionaries
            criteria: Job criteria object
            job_description: Full job description text
            
        Returns:
            List of evaluation result dictionaries (same format as evaluate_applicant)
        """
        pass
    
    @abstractmethod
    def generate_interview_questions(
        self,
        applicant_data: Dict[str, Any],
        job_description: str,
        config: Dict[str, Any] = None 
    ) -> List[Dict[str, Any]]:
        """
        Generate specific interview questions for a candidate.
        
        Args:
            applicant_data: Dictionary containing applicant information
            job_description: Full job description text
            config: Optional configuration (counts of different question types)
            
        Returns:
            List of dictionaries forming the interview guide.
        """
        pass
    @abstractmethod
    def chat_with_candidate(
        self,
        query: str,
        applicant_data: Dict[str, Any],
        job_description: str,
        chat_history: List[Dict[str, Any]]
    ) -> str:
        """
        Chat with the candidate's profile (The Investigator).
        
        Args:
            query: The user's question
            applicant_data: The candidate's profile data
            job_description: The job description
            chat_history: Previous messages [ {"role": "user", "content": "..."}, ... ]
            
        Returns:
            The AI's response string
        """
        pass
    def _determine_tier(self, score: int) -> int:
        """
        Determine tier based on score.
        
        Tier 1 (85-100): Auto-advance candidates
        Tier 2 (70-84): Review recommended  
        Tier 3 (0-69): Auto-decline or low priority
        
        Args:
            score: Applicant score (0-100)
            
        Returns:
            Tier number (1, 2, or 3)
        """
        if score >= 85:
            return 1
        elif score >= 70:
            return 2
        else:
            return 3
