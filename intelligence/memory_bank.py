"""
Memory Bank.
Persistent local storage (SQLite) for self-learned intelligence and breach data.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime

class MemoryBank:
    """Manages local intelligence storage."""
    
    def __init__(self, db_path: str = "data/memory_bank.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Identity Table (The core entities)
        c.execute('''CREATE TABLE IF NOT EXISTS identities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT, -- email, username, phone, password, hash
            value TEXT,
            context TEXT, -- Related info (full line, json context)
            source TEXT, -- Filename or origin
            confidence REAL,
            created_at TIMESTAMP
        )''')
        
        # Indexes for fast search
        c.execute('CREATE INDEX IF NOT EXISTS idx_value ON identities(value)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_type ON identities(type)')
        
        conn.commit()
        conn.close()

    def store_entity(self, type: str, value: str, source: str, context: str = "", confidence: float = 1.0):
        """Store a discovered entity."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Upsert logic (simplified: ignore if exists or just add duplicate entry for frequency analysis?)
            # Ideally we want unique value/type pairs but with different sources.
            # For simplicity, we just insert.
            
            c.execute('''INSERT INTO identities (type, value, source, context, confidence, created_at)
                      VALUES (?, ?, ?, ?, ?, ?)''',
                      (type, value, source, context, confidence, datetime.now()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"DB Error: {e}")

    def search(self, query: str) -> List[Dict]:
        """Search the memory bank."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Exact match
        c.execute('SELECT * FROM identities WHERE value = ?', (query,))
        rows = c.fetchall()
        
        # If no exact match, try LIKE
        if not rows:
            c.execute('SELECT * FROM identities WHERE value LIKE ? OR context LIKE ?', (f'%{query}%', f'%{query}%'))
            rows = c.fetchall()
            
        results = [dict(row) for row in rows]
        conn.close()
        return results

    def get_stats(self) -> Dict[str, int]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM identities')
        total = c.fetchone()[0]
        conn.close()
        return {'total_entities': total}

    def deduplicate(self):
        """Remove exact duplicates and clean up data."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Simple SQL deduction: Delete rows where ID is not the MIN ID for that value/type
            c.execute('''
            DELETE FROM identities 
            WHERE id NOT IN (
                SELECT MIN(id) 
                FROM identities 
                GROUP BY value, type
            )
            ''')
            
            deleted = c.rowcount
            conn.commit()
            conn.close()
            logger.info(f"[MemoryBank] Deduplication complete. Removed {deleted} duplicate entries.")
            return deleted
        except Exception as e:
            logger.error(f"[MemoryBank] Deduplication failed: {e}")
            return 0
