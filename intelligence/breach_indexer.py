#!/usr/bin/env python3
"""
Breach Database Indexer

Processes, deduplicates, and indexes leaked credentials into searchable format.
"""

import re
import sqlite3
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime
from loguru import logger
import mmh3  # MurmurHash for fast deduplication


class BreachIndexer:
    """Indexes and searches breach databases."""
    
    # Credential pattern matchers
    EMAIL_PASS_PATTERNS = [
        r'([\w\.-]+@[\w\.-]+\.\w+)\s*[:;|]\s*(.+)',  # email:password
        r'([\w\.-]+@[\w\.-]+\.\w+)\s+(.+)',  # email password
    ]
    
    HASH_PATTERNS = {
        'md5': re.compile(r'\b([a-f0-9]{32})\b', re.IGNORECASE),
        'sha1': re.compile(r'\b([a-f0-9]{40})\b', re.IGNORECASE),
        'sha256': re.compile(r'\b([a-f0-9]{64})\b', re.IGNORECASE),
    }
    
    def __init__(self, db_path: Path = None):
        """Initialize indexer."""
        self.db_path = db_path or Path("data/breach_vault/breach_index.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        self._init_database()
        logger.info(f"BreachIndexer initialized: {self.db_path}")
    
    def _init_database(self):
        """Initialize database schema."""
        # Credentials table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                password TEXT,
                password_hash TEXT,
                hash_type TEXT,
                source TEXT,
                breach_name TEXT,
                breach_date TEXT,
                added_date TEXT,
                murmur_hash INTEGER,
                UNIQUE(email, password)
            )
        ''')
        
        # Create indexes for fast searching
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_email 
            ON credentials(email)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_murmur_hash 
            ON credentials(murmur_hash)
        ''')
        
        # Breach metadata table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS breaches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                source TEXT,
                date TEXT,
                record_count INTEGER,
                file_path TEXT,
                processed_date TEXT,
                data_types TEXT
            )
        ''')
        
        # Statistics table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated TEXT
            )
        ''')
        
        self.conn.commit()
    
    def _extract_credentials(self, content: str) -> List[Tuple[str, str]]:
        """Extract email:password pairs from text content."""
        credentials = []
        
        for pattern in self.EMAIL_PASS_PATTERNS:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                email = match.group(1).strip().lower()
                password = match.group(2).strip()
                
                # Basic validation
                if len(email) > 5 and '@' in email and len(password) > 0:
                    credentials.append((email, password))
        
        return credentials
    
    def _detect_hash_type(self, value: str) -> Optional[str]:
        """Detect hash type from string."""
        for hash_type, pattern in self.HASH_PATTERNS.items():
            if pattern.match(value):
                return hash_type
        return None
    
    def _compute_murmur(self, email: str, password: str) -> int:
        """Compute MurmurHash3 for deduplication."""
        combo = f"{email}:{password}".encode('utf-8')
        return mmh3.hash(combo)
    
    def index_file(self, file_path: Path, breach_name: str = None, 
                   breach_date: str = None) -> Dict:
        """Index a breach file."""
        logger.info(f"Indexing breach file: {file_path}")
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return {'error': 'File not found'}
        
        stats = {
            'file': str(file_path),
            'total_lines': 0,
            'credentials_found': 0,
            'duplicates_skipped': 0,
            'indexed': 0,
            'errors': 0
        }
        
        try:
            # Read file
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()
            stats['total_lines'] = len(lines)
            
            # Extract credentials
            credentials = self._extract_credentials(content)
            stats['credentials_found'] = len(credentials)
            
            if not breach_name:
                breach_name = file_path.stem
            
            if not breach_date:
                breach_date = datetime.utcnow().strftime('%Y-%m-%d')
            
            # Register breach
            try:
                self.cursor.execute('''
                    INSERT OR IGNORE INTO breaches 
                    (name, source, date, file_path, processed_date, record_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    breach_name,
                    'file_upload',
                    breach_date,
                    str(file_path),
                    datetime.utcnow().isoformat(),
                    len(credentials)
                ))
                self.conn.commit()
            except sqlite3.IntegrityError:
                pass  # Breach already registered
            
            # Index credentials
            for email, password in credentials:
                try:
                    # Compute hash for deduplication
                    murmur = self._compute_murmur(email, password)
                    
                    # Check if hash password
                    hash_type = self._detect_hash_type(password)
                    
                    # Insert credential
                    try:
                        self.cursor.execute('''
                            INSERT INTO credentials
                            (email, password, password_hash, hash_type, source, 
                             breach_name, breach_date, added_date, murmur_hash)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            email,
                            password if not hash_type else None,
                            password if hash_type else None,
                            hash_type,
                            'file',
                            breach_name,
                            breach_date,
                            datetime.utcnow().isoformat(),
                            murmur
                        ))
                        stats['indexed'] += 1
                    except sqlite3.IntegrityError:
                        stats['duplicates_skipped'] += 1
                
                except Exception as e:
                    stats['errors'] += 1
                    if stats['errors'] < 10:  # Log first 10 errors
                        logger.error(f"Error indexing credential: {e}")
            
            self.conn.commit()
            
            # Update statistics
            self._update_stats()
            
            logger.info(f"Indexing complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"File indexing error: {e}")
            return {'error': str(e)}
    
    def search_email(self, email: str) -> List[Dict]:
        """Search for email in breach database."""
        email = email.strip().lower()
        
        self.cursor.execute('''
            SELECT email, password, password_hash, hash_type, 
                   breach_name, breach_date, source
            FROM credentials
            WHERE email = ?
            ORDER BY breach_date DESC
        ''', (email,))
        
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'email': row[0],
                'password': row[1],
                'password_hash': row[2],
                'hash_type': row[3],
                'breach': row[4],
                'date': row[5],
                'source': row[6]
            })
        
        return results
    
    def search_domain(self, domain: str) -> List[Dict]:
        """Search for all emails from a domain."""
        domain = domain.strip().lower()
        
        self.cursor.execute('''
            SELECT DISTINCT email, COUNT(*) as breach_count
            FROM credentials
            WHERE email LIKE ?
            GROUP BY email
            ORDER BY breach_count DESC
            LIMIT 1000
        ''', (f'%@{domain}%',))
        
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'email': row[0],
                'breach_count': row[1]
            })
        
        return results
    
    def get_breach_stats(self) -> Dict:
        """Get breach database statistics."""
        stats = {}
        
        # Total credentials
        self.cursor.execute('SELECT COUNT(*) FROM credentials')
        stats['total_credentials'] = self.cursor.fetchone()[0]
        
        # Unique emails
        self.cursor.execute('SELECT COUNT(DISTINCT email) FROM credentials')
        stats['unique_emails'] = self.cursor.fetchone()[0]
        
        # Total breaches
        self.cursor.execute('SELECT COUNT(*) FROM breaches')
        stats['total_breaches'] = self.cursor.fetchone()[0]
        
        # Recent breaches
        self.cursor.execute('''
            SELECT name, date, record_count
            FROM breaches
            ORDER BY processed_date DESC
            LIMIT 10
        ''')
        stats['recent_breaches'] = [
            {'name': row[0], 'date': row[1], 'records': row[2]}
            for row in self.cursor.fetchall()
        ]
        
        # Top domains
        self.cursor.execute('''
            SELECT 
                SUBSTR(email, INSTR(email, '@') + 1) as domain,
                COUNT(*) as count
            FROM credentials
            GROUP BY domain
            ORDER BY count DESC
            LIMIT 10
        ''')
        stats['top_domains'] = [
            {'domain': row[0], 'count': row[1]}
            for row in self.cursor.fetchall()
        ]
        
        return stats
    
    def _update_stats(self):
        """Update statistics table."""
        stats = self.get_breach_stats()
        
        for key, value in stats.items():
            if not isinstance(value, list):
                self.cursor.execute('''
                    INSERT OR REPLACE INTO stats (key, value, updated)
                    VALUES (?, ?, ?)
                ''', (key, str(value), datetime.utcnow().isoformat()))
        
        self.conn.commit()
    
    def optimize_database(self):
        """Optimize database performance."""
        logger.info("Optimizing database...")
        self.cursor.execute('VACUUM')
        self.cursor.execute('ANALYZE')
        self.conn.commit()
        logger.info("Database optimized")
    
    def __del__(self):
        """Close database connection."""
        if hasattr(self, 'conn'):
            self.conn.close()


if __name__ == '__main__':
    indexer = BreachIndexer()
    print(indexer.get_breach_stats())
