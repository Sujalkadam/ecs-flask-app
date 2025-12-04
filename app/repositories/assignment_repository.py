from typing import Optional, List
from datetime import datetime
from ..models import ItemAssignment
from ..extensions import db


class AssignmentRepository:
    """Data access layer for ItemAssignment operations"""

    @staticmethod
    def find_by_id(assignment_id: int) -> Optional[ItemAssignment]:
        """Find assignment by ID"""
        return ItemAssignment.query.get(assignment_id)

    @staticmethod
    def find_by_staff_id(staff_id: int) -> List[ItemAssignment]:
        """Find all assignments for a staff member"""
        return ItemAssignment.query.filter_by(
            staff_id=staff_id
        ).order_by(ItemAssignment.created_at.desc()).all()

    @staticmethod
    def get_pending_returns() -> List[ItemAssignment]:
        """Get all assignments with return_requested status"""
        return ItemAssignment.query.filter_by(
            status="return_requested"
        ).order_by(ItemAssignment.updated_at.desc()).all()

    @staticmethod
    def get_active_assignments_count() -> int:
        """Get count of active assignments"""
        return ItemAssignment.query.filter_by(status="assigned").count()

    @staticmethod
    def get_pending_returns_count() -> int:
        """Get count of pending returns"""
        return ItemAssignment.query.filter_by(status="return_requested").count()

    @staticmethod
    def create(item_id: int, staff_id: int, allocation_date=None) -> ItemAssignment:
        """Create a new assignment"""
        if allocation_date is None:
            allocation_date = datetime.utcnow()
        
        assignment = ItemAssignment(
            item_id=item_id,
            staff_id=staff_id,
            allocation_date=allocation_date,
            status="assigned",
        )
        db.session.add(assignment)
        db.session.commit()
        return assignment

    @staticmethod
    def update_status(assignment: ItemAssignment, status: str) -> ItemAssignment:
        """Update assignment status"""
        assignment.status = status
        db.session.commit()
        return assignment

    @staticmethod
    def request_return(assignment: ItemAssignment) -> ItemAssignment:
        """Mark assignment as return requested"""
        assignment.status = "return_requested"
        db.session.commit()
        return assignment

    @staticmethod
    def complete_return(assignment: ItemAssignment) -> ItemAssignment:
        """Complete return and update return date"""
        assignment.status = "returned"
        assignment.return_date = datetime.utcnow()
        db.session.commit()
        return assignment

    @staticmethod
    def delete_by_item_id(item_id: int) -> int:
        """Delete all assignments for an item"""
        count = ItemAssignment.query.filter_by(item_id=item_id).delete()
        db.session.commit()
        return count

    @staticmethod
    def delete_by_staff_id(staff_id: int) -> int:
        """Delete all assignments for a staff member"""
        count = ItemAssignment.query.filter_by(staff_id=staff_id).delete()
        db.session.commit()
        return count

