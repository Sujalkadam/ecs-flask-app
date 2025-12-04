from typing import Optional, List
from ..models import StaffUser
from ..extensions import db


class StaffRepository:
    """Data access layer for StaffUser operations"""

    @staticmethod
    def find_by_email(email: str) -> Optional[StaffUser]:
        """Find staff user by email"""
        return StaffUser.query.filter_by(email=email.lower()).first()

    @staticmethod
    def find_by_id(staff_id: int) -> Optional[StaffUser]:
        """Find staff user by ID"""
        return StaffUser.query.get(staff_id)

    @staticmethod
    def create(full_name: str, email: str, password_hash: str, department: str = None) -> StaffUser:
        """Create a new staff user"""
        staff = StaffUser(
            full_name=full_name.strip(),
            email=email.lower(),
            password_hash=password_hash,
            department=department,
        )
        db.session.add(staff)
        db.session.commit()
        return staff

    @staticmethod
    def get_all() -> List[StaffUser]:
        """Get all staff users"""
        return StaffUser.query.order_by(StaffUser.full_name.asc()).all()

    @staticmethod
    def get_all_for_choices() -> List[tuple]:
        """Get all staff users formatted for form choices"""
        staff_members = StaffRepository.get_all()
        return [(member.id, member.full_name) for member in staff_members]

