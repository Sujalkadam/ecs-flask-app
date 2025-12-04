"""Transaction management utilities for service layer"""
from contextlib import contextmanager
from ..extensions import db


@contextmanager
def transaction():
    """
    Context manager for database transactions.
    Automatically commits on success, rolls back on exception.
    """
    try:
        yield
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

