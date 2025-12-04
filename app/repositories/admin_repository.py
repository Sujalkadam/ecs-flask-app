from typing import Optional
from ..models import AdminUser
from ..extensions import db


class AdminRepository:
    """Data access layer for AdminUser operations"""

    @staticmethod
    def find_by_email(email: str) -> Optional[AdminUser]:
        """Find admin user by email"""
        return AdminUser.query.filter_by(email=email.lower()).first()

    @staticmethod
    def find_by_id(admin_id: int) -> Optional[AdminUser]:
        """Find admin user by ID"""
        return AdminUser.query.get(admin_id)

    @staticmethod
    def create(full_name: str, email: str, password_hash: str) -> AdminUser:
        """Create a new admin user"""
        admin = AdminUser(
            full_name=full_name.strip(),
            email=email.lower(),
            password_hash=password_hash,
        )
        db.session.add(admin)
        db.session.commit()
        return admin

    @staticmethod
    def get_all():
        """Get all admin users"""
        return AdminUser.query.all()

