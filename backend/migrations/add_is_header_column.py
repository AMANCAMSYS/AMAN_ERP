"""
Migration: Add is_header column to accounts table
Date: 2026-03-03
Purpose: Track which accounts are header (parent/group) accounts vs detail (posting) accounts
"""

from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


def migrate(db):
    """Add is_header column to accounts table if it doesn't exist."""
    try:
        # Check if column already exists
        exists = db.execute(text("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'accounts' AND column_name = 'is_header'
        """)).scalar()
        
        if exists:
            logger.info("✅ is_header column already exists")
            return True
        
        # Add the column
        db.execute(text("""
            ALTER TABLE accounts ADD COLUMN is_header BOOLEAN DEFAULT FALSE
        """))
        
        # Auto-detect header accounts: any account that has children is a header
        db.execute(text("""
            UPDATE accounts SET is_header = TRUE
            WHERE id IN (SELECT DISTINCT parent_id FROM accounts WHERE parent_id IS NOT NULL)
        """))
        
        db.commit()
        logger.info("✅ Added is_header column to accounts table")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Migration failed: {e}")
        return False
