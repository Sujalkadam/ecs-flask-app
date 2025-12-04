from typing import Optional, List
from sqlalchemy import func, or_
from ..models import InventoryItem
from ..extensions import db


class InventoryRepository:
    """Data access layer for InventoryItem operations"""

    @staticmethod
    def find_by_id(item_id: int) -> Optional[InventoryItem]:
        """Find inventory item by ID"""
        return InventoryItem.query.get(item_id)

    @staticmethod
    def get_all() -> List[InventoryItem]:
        """Get all inventory items"""
        return InventoryItem.query.order_by(InventoryItem.created_at.desc()).all()

    @staticmethod
    def search(query: str) -> List[InventoryItem]:
        """Search inventory items by name or category"""
        pattern = f"%{query}%"
        return InventoryItem.query.filter(
            or_(
                InventoryItem.name.ilike(pattern),
                InventoryItem.category.ilike(pattern),
            )
        ).order_by(InventoryItem.created_at.desc()).all()

    @staticmethod
    def get_available_items() -> List[InventoryItem]:
        """Get all items with quantity > 0"""
        return InventoryItem.query.filter(
            InventoryItem.quantity_available > 0
        ).order_by(InventoryItem.name.asc()).all()

    @staticmethod
    def get_available_items_for_choices() -> List[tuple]:
        """Get available items formatted for form choices"""
        items = InventoryRepository.get_available_items()
        return [
            (item.id, f"{item.name} · {item.quantity_available} available")
            for item in items
        ]

    @staticmethod
    def get_latest(limit: int = 3) -> List[InventoryItem]:
        """Get latest inventory items"""
        return InventoryItem.query.order_by(
            InventoryItem.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def get_low_stock(threshold: int = 3) -> List[InventoryItem]:
        """Get items with quantity <= threshold"""
        return InventoryItem.query.filter(
            InventoryItem.quantity_available <= threshold
        ).order_by(InventoryItem.quantity_available.asc()).all()

    @staticmethod
    def create(name: str, category: str, quantity: int, purchase_date=None, price=None) -> InventoryItem:
        """Create a new inventory item"""
        item = InventoryItem(
            name=name.strip(),
            category=category.strip(),
            quantity_available=quantity,
            purchase_date=purchase_date,
            price=price,
        )
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def update(item: InventoryItem, name: str, category: str, quantity: int, purchase_date=None, price=None) -> InventoryItem:
        """Update an existing inventory item"""
        item.name = name.strip()
        item.category = category.strip()
        item.quantity_available = quantity
        item.purchase_date = purchase_date
        item.price = price
        db.session.commit()
        return item

    @staticmethod
    def delete(item_id: int) -> bool:
        """Delete an inventory item"""
        item = InventoryRepository.find_by_id(item_id)
        if item:
            db.session.delete(item)
            db.session.commit()
            return True
        return False

    @staticmethod
    def decrement_quantity(item: InventoryItem, amount: int = 1) -> InventoryItem:
        """Decrement item quantity"""
        item.quantity_available -= amount
        db.session.commit()
        return item

    @staticmethod
    def increment_quantity(item: InventoryItem, amount: int = 1) -> InventoryItem:
        """Increment item quantity"""
        item.quantity_available += amount
        db.session.commit()
        return item

    @staticmethod
    def get_count() -> int:
        """Get total count of inventory items"""
        return InventoryItem.query.count()

    @staticmethod
    def get_total_quantity() -> int:
        """Get total quantity of all items"""
        result = db.session.query(
            func.coalesce(func.sum(InventoryItem.quantity_available), 0)
        ).scalar()
        return int(result) if result else 0

    @staticmethod
    def get_average_price():
        """Get average price of all items"""
        return db.session.query(func.avg(InventoryItem.price)).scalar()

