from typing import Optional, Dict
from werkzeug.security import check_password_hash, generate_password_hash
from ..models import AdminUser
from ..repositories import AdminRepository


class AdminService:
    """Business logic layer for Admin operations"""

    @staticmethod
    def authenticate(email: str, password: str) -> Optional[AdminUser]:
        """
        Authenticate admin user
        Returns AdminUser if credentials are valid, None otherwise
        """
        admin = AdminRepository.find_by_email(email)
        if admin and check_password_hash(admin.password_hash, password):
            return admin
        return None

    @staticmethod
    def register(full_name: str, email: str, password: str) -> AdminUser:
        """
        Register a new admin user
        Returns the created AdminUser
        """
        # Check if admin already exists
        existing = AdminRepository.find_by_email(email)
        if existing:
            raise ValueError("Admin with this email already exists")
        
        password_hash = generate_password_hash(password)
        return AdminRepository.create(full_name, email, password_hash)

    @staticmethod
    def get_dashboard_stats() -> Dict:
        """
        Get dashboard statistics for admin
        Returns dictionary with stats
        """
        from ..repositories import InventoryRepository, RequestRepository, AssignmentRepository
        
        return {
            "inventory_count": InventoryRepository.get_count(),
            "inventory_quantity": InventoryRepository.get_total_quantity(),
            "pending_requests": RequestRepository.get_pending_count(),
            "pending_returns": AssignmentRepository.get_pending_returns_count(),
        }

