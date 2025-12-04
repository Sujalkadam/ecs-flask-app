from typing import List, Dict, Optional
from ..models import Feedback
from ..repositories import FeedbackRepository


class FeedbackService:
    """Business logic layer for Feedback operations"""

    @staticmethod
    def submit_feedback(staff_id: int, rating: int, question_1: str = None, question_2: str = None,
                       question_3: str = None, question_4: str = None, question_5: str = None) -> Feedback:
        """
        Submit feedback
        Validates rating range
        """
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        
        return FeedbackRepository.create(
            staff_id, rating, question_1, question_2, question_3, question_4, question_5
        )

    @staticmethod
    def get_recent_feedback(limit: int = 10) -> List[Feedback]:
        """Get recent feedback entries"""
        return FeedbackRepository.get_recent(limit)

    @staticmethod
    def get_stats() -> Dict:
        """Get feedback statistics"""
        return {
            "total_feedback": FeedbackRepository.get_count(),
            "average_rating": FeedbackRepository.get_average_rating(),
        }

