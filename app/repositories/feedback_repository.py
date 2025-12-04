from typing import List
from sqlalchemy import func
from ..models import Feedback
from ..extensions import db


class FeedbackRepository:
    """Data access layer for Feedback operations"""

    @staticmethod
    def create(staff_id: int, rating: int, question_1: str = None, question_2: str = None,
               question_3: str = None, question_4: str = None, question_5: str = None) -> Feedback:
        """Create a new feedback entry"""
        feedback = Feedback(
            staff_id=staff_id,
            rating=rating,
            question_1=question_1.strip() if question_1 else None,
            question_2=question_2.strip() if question_2 else None,
            question_3=question_3.strip() if question_3 else None,
            question_4=question_4.strip() if question_4 else None,
            question_5=question_5.strip() if question_5 else None,
        )
        db.session.add(feedback)
        db.session.commit()
        return feedback

    @staticmethod
    def get_recent(limit: int = 10) -> List[Feedback]:
        """Get recent feedback entries"""
        return Feedback.query.order_by(
            Feedback.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def get_count() -> int:
        """Get total count of feedback entries"""
        return Feedback.query.count()

    @staticmethod
    def get_average_rating():
        """Get average rating"""
        return db.session.query(func.avg(Feedback.rating)).scalar()

