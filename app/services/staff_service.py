from typing import Optional
from werkzeug.security import check_password_hash, generate_password_hash
from ..models import StaffUser
from ..repositories import StaffRepository


class StaffService:
    """Business logic layer for Staff operations"""

    @staticmethod
    def authenticate(email: str, password: str) -> Optional[StaffUser]:
        """
        Authenticate staff user
        Returns StaffUser if credentials are valid, None otherwise
        """
        staff = StaffRepository.find_by_email(email)
        if staff and check_password_hash(staff.password_hash, password):
            return staff
        return None

    @staticmethod
    def register(full_name: str, email: str, password: str, department: str = None) -> StaffUser:
        """
        Register a new staff user
        Returns the created StaffUser
        """
        # Check if staff already exists
        existing = StaffRepository.find_by_email(email)
        if existing:
            raise ValueError("Staff with this email already exists")
        
        password_hash = generate_password_hash(password)
        return StaffRepository.create(full_name, email, password_hash, department)

    @staticmethod
    def get_staff_for_choices() -> list:
        """Get all staff members formatted for form choices"""
        return StaffRepository.get_all_for_choices()

    @staticmethod
    def get_staff(staff_id: int) -> Optional[StaffUser]:
        """Get staff user by ID"""
        return StaffRepository.find_by_id(staff_id)

