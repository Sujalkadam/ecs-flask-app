from typing import Optional, List, Dict
from decimal import Decimal
from ..models import InventoryItem
from ..repositories import InventoryRepository


class InventoryService:
    """Business logic layer for Inventory operations"""

    @staticmethod
    def get_item(item_id: int) -> Optional[InventoryItem]:
        """Get inventory item by ID"""
        return InventoryRepository.find_by_id(item_id)

    @staticmethod
    def list_items(search_query: str = None) -> List[InventoryItem]:
        """List all inventory items, optionally filtered by search"""
        if search_query and search_query.strip():
            return InventoryRepository.search(search_query.strip())
        return InventoryRepository.get_all()

    @staticmethod
    def get_stats() -> Dict:
        """Get inventory statistics"""
        return {
            "total_items": InventoryRepository.get_count(),
            "total_quantity": InventoryRepository.get_total_quantity(),
            "average_price": InventoryRepository.get_average_price(),
        }

    @staticmethod
    def create_item(name: str, category: str, quantity: int, purchase_date=None, price=None) -> InventoryItem:
        """
        Create a new inventory item
        Validates business rules before creation
        """
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        
        if price is not None and price < 0:
            raise ValueError("Price cannot be negative")
        
        return InventoryRepository.create(name, category, quantity, purchase_date, price)

    @staticmethod
    def update_item(item_id: int, name: str, category: str, quantity: int, purchase_date=None, price=None) -> InventoryItem:
        """
        Update an existing inventory item
        Validates business rules before update
        """
        item = InventoryRepository.find_by_id(item_id)
        if not item:
            raise ValueError("Item not found")
        
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        
        if price is not None and price < 0:
            raise ValueError("Price cannot be negative")
        
        return InventoryRepository.update(item, name, category, quantity, purchase_date, price)

    @staticmethod
    def delete_item(item_id: int) -> bool:
        """
        Delete an inventory item
        Also deletes related assignments to maintain referential integrity
        """
        from ..repositories import AssignmentRepository
        from .transaction_manager import transaction
        
        item = InventoryRepository.find_by_id(item_id)
        if not item:
            return False
        
        try:
            with transaction():
                # Delete related assignments first
                AssignmentRepository.delete_by_item_id(item_id)
                # Delete item in same transaction
                InventoryRepository.delete(item_id)
            return True
        except Exception:
            return False

    @staticmethod
    def get_available_items_for_choices() -> List[tuple]:
        """Get available items formatted for form choices"""
        return InventoryRepository.get_available_items_for_choices()

    @staticmethod
    def get_latest_items(limit: int = 3) -> List[InventoryItem]:
        """Get latest inventory items"""
        return InventoryRepository.get_latest(limit)

    @staticmethod
    def get_low_stock_items(threshold: int = 3) -> List[InventoryItem]:
        """Get items with low stock"""
        return InventoryRepository.get_low_stock(threshold)

    @staticmethod
    def is_item_available(item_id: int) -> bool:
        """Check if item is available (quantity > 0)"""
        item = InventoryRepository.find_by_id(item_id)
        return item is not None and item.quantity_available > 0

