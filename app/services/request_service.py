from typing import Optional, List, Dict
from datetime import datetime
from ..models import ItemRequest, InventoryItem, ItemAssignment
from ..extensions import db
from ..repositories import RequestRepository, AssignmentRepository, InventoryRepository
from .transaction_manager import transaction


class RequestService:
    """Business logic layer for Request operations"""

    @staticmethod
    def get_requests_for_staff(staff_id: int) -> List[ItemRequest]:
        """Get all requests for a staff member"""
        return RequestRepository.find_by_staff_id(staff_id)

    @staticmethod
    def get_pending_requests() -> List[ItemRequest]:
        """Get all pending requests"""
        return RequestRepository.get_pending()

    @staticmethod
    def get_request_history(limit: int = 10) -> List[ItemRequest]:
        """Get request history"""
        return RequestRepository.get_history(limit)

    @staticmethod
    def create_request(staff_id: int, item_name: str, justification: str = None) -> ItemRequest:
        """
        Create a new item request
        Validates business rules
        """
        if not item_name or not item_name.strip():
            raise ValueError("Item name is required")
        
        return RequestRepository.create(staff_id, item_name.strip(), justification)

    @staticmethod
    def approve_request(request_id: int, item_id: int) -> Dict:
        """
        Approve a request and create assignment atomically
        Returns dictionary with assignment and request
        """
        with transaction():
            # Get request and validate
            request = RequestRepository.find_by_id(request_id)
            if not request:
                raise ValueError("Request not found")
            
            if request.status != "pending":
                raise ValueError("This request has already been processed")
            
            # Lock item row to prevent race conditions
            item = db.session.query(InventoryItem).filter_by(id=item_id).with_for_update().first()
            if not item:
                raise ValueError("Item not found")
            
            if item.quantity_available <= 0:
                raise ValueError("Item is no longer available")
            
            # Create assignment
            assignment = ItemAssignment(
                item_id=item_id,
                staff_id=request.staff_id,
                allocation_date=datetime.utcnow(),
                status="assigned",
            )
            db.session.add(assignment)
            
            # Decrement quantity
            item.quantity_available -= 1
            
            # Update request status
            request.status = "approved"
            
            # Single commit for all operations
            return {
                "assignment": assignment,
                "request": request,
            }

    @staticmethod
    def reject_request(request_id: int) -> ItemRequest:
        """
        Reject a request
        Validates request status
        """
        request = RequestRepository.find_by_id(request_id)
        if not request:
            raise ValueError("Request not found")
        
        if request.status != "pending":
            raise ValueError("This request has already been processed")
        
        return RequestRepository.reject(request)

    @staticmethod
    def get_pending_count() -> int:
        """Get count of pending requests"""
        return RequestRepository.get_pending_count()

