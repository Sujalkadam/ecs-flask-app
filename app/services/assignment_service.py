from typing import Optional, List
from datetime import datetime
from ..models import ItemAssignment, InventoryItem
from ..extensions import db
from ..repositories import AssignmentRepository, InventoryRepository
from .transaction_manager import transaction


class AssignmentService:
    """Business logic layer for Assignment operations"""

    @staticmethod
    def get_assignments_for_staff(staff_id: int) -> List[ItemAssignment]:
        """Get all assignments for a staff member"""
        return AssignmentRepository.find_by_staff_id(staff_id)

    @staticmethod
    def get_pending_returns() -> List[ItemAssignment]:
        """Get all assignments pending return"""
        return AssignmentRepository.get_pending_returns()

    @staticmethod
    def create_assignment(item_id: int, staff_id: int) -> ItemAssignment:
        """
        Create a new assignment
        Validates item availability and decrements quantity atomically
        """
        with transaction():
            # Use SELECT FOR UPDATE to lock the row and prevent race conditions
            item = db.session.query(InventoryItem).filter_by(id=item_id).with_for_update().first()
            if not item:
                raise ValueError("Item not found")
            
            if item.quantity_available <= 0:
                raise ValueError("Item is not available")
            
            # Create assignment
            assignment = ItemAssignment(
                item_id=item_id,
                staff_id=staff_id,
                allocation_date=datetime.utcnow(),
                status="assigned",
            )
            db.session.add(assignment)
            
            # Decrement quantity in the same transaction
            item.quantity_available -= 1
            
            # Single commit for both operations
            return assignment

    @staticmethod
    def request_return(assignment_id: int, staff_id: int) -> ItemAssignment:
        """
        Request return of an assignment
        Validates ownership and current status
        """
        assignment = AssignmentRepository.find_by_id(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")
        
        if assignment.staff_id != staff_id:
            raise ValueError("You can only return your own assignments")
        
        if assignment.status not in {"assigned", "return_requested"}:
            raise ValueError("This item cannot be returned right now")
        
        if assignment.status == "return_requested":
            raise ValueError("Return already requested")
        
        return AssignmentRepository.request_return(assignment)

    @staticmethod
    def complete_return(assignment_id: int) -> ItemAssignment:
        """
        Complete return of an assignment
        Validates status and increments item quantity atomically
        """
        with transaction():
            # Query directly in transaction to avoid separate commits
            assignment = db.session.query(ItemAssignment).filter_by(id=assignment_id).first()
            if not assignment:
                raise ValueError("Assignment not found")
            
            if assignment.status != "return_requested":
                raise ValueError("This assignment is not pending return")
            
            # Update assignment status and return date
            assignment.status = "returned"
            assignment.return_date = datetime.utcnow()
            
            # Increment quantity if item exists (in same transaction)
            if assignment.item:
                # Refresh item to get latest state
                db.session.refresh(assignment.item)
                assignment.item.quantity_available += 1
            
            # Single commit for both operations
            return assignment

    @staticmethod
    def get_active_assignments_count() -> int:
        """Get count of active assignments"""
        return AssignmentRepository.get_active_assignments_count()

    @staticmethod
    def get_pending_returns_count() -> int:
        """Get count of pending returns"""
        return AssignmentRepository.get_pending_returns_count()

