from typing import Optional, List
from ..models import ItemRequest
from ..extensions import db


class RequestRepository:
    """Data access layer for ItemRequest operations"""

    @staticmethod
    def find_by_id(request_id: int) -> Optional[ItemRequest]:
        """Find request by ID"""
        return ItemRequest.query.get(request_id)

    @staticmethod
    def find_by_staff_id(staff_id: int) -> List[ItemRequest]:
        """Find all requests for a staff member"""
        return ItemRequest.query.filter_by(
            staff_id=staff_id
        ).order_by(ItemRequest.created_at.desc()).all()

    @staticmethod
    def get_pending() -> List[ItemRequest]:
        """Get all pending requests"""
        return ItemRequest.query.filter_by(
            status="pending"
        ).order_by(ItemRequest.created_at.asc()).all()

    @staticmethod
    def get_pending_count() -> int:
        """Get count of pending requests"""
        return ItemRequest.query.filter_by(status="pending").count()

    @staticmethod
    def get_history(limit: int = 10) -> List[ItemRequest]:
        """Get request history (non-pending)"""
        return ItemRequest.query.filter(
            ItemRequest.status != "pending"
        ).order_by(ItemRequest.updated_at.desc()).limit(limit).all()

    @staticmethod
    def create(staff_id: int, item_name: str, justification: str = None) -> ItemRequest:
        """Create a new request"""
        request = ItemRequest(
            staff_id=staff_id,
            item_name=item_name.strip(),
            justification=justification.strip() if justification else None,
        )
        db.session.add(request)
        db.session.commit()
        return request

    @staticmethod
    def update_status(request: ItemRequest, status: str) -> ItemRequest:
        """Update request status"""
        request.status = status
        db.session.commit()
        return request

    @staticmethod
    def approve(request: ItemRequest) -> ItemRequest:
        """Approve a request"""
        return RequestRepository.update_status(request, "approved")

    @staticmethod
    def reject(request: ItemRequest) -> ItemRequest:
        """Reject a request"""
        return RequestRepository.update_status(request, "rejected")

    @staticmethod
    def delete_by_staff_id(staff_id: int) -> int:
        """Delete all requests for a staff member"""
        count = ItemRequest.query.filter_by(staff_id=staff_id).delete()
        db.session.commit()
        return count

