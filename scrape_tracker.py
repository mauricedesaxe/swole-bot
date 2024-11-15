import sqlite3
from datetime import datetime, timezone
import os
from typing import Optional, Tuple, List
from urllib.parse import urlparse

class ScrapeTracker:
    def __init__(self, db_name: str = "scrape_tracker.db"):
        self.db_name = db_name
        self.db_path = os.path.join("./db", db_name)
        self.init_db()

    def init_db(self):
        """Initializes the database in the ./db directory."""
        # Create the db directory if it doesn't exist
        db_dir = "./db"
        os.makedirs(db_dir, exist_ok=True)

        # create the table
        db_path = os.path.join(db_dir, self.db_name)
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraped_urls (
                    url TEXT PRIMARY KEY,
                    file_path TEXT,
                    status TEXT CHECK(status IN ('pending', 'in_progress', 'completed', 'failed')) DEFAULT 'pending',
                    priority INTEGER DEFAULT 0,
                    error_message TEXT,
                    last_successfully_scraped TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create trigger to update updated_at timestamp
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_timestamp 
                AFTER UPDATE ON scraped_urls
                FOR EACH ROW
                BEGIN
                    UPDATE scraped_urls SET updated_at = CURRENT_TIMESTAMP
                    WHERE url = NEW.url;
                END;
            ''')
            conn.commit()

    def add_todo_url(self, url: str, priority: int = 0) -> None:
        """Add a new URL to be scraped."""
        if not self.is_valid_url(url):
            raise ValueError("Invalid URL format")
        
        url = self._normalize_url(url)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO scraped_urls 
                (url, status, priority)
                VALUES (?, 'pending', ?)
            ''', (url, priority))
            conn.commit()

    def update_url_status(self, url: str, status: str, error_message: str = None, file_path: str = None) -> None:
        """Update the status of a URL."""
        if not self.is_valid_url(url):
            raise ValueError("Invalid URL format")
        
        if status not in ('pending', 'in_progress', 'completed', 'failed'):
            raise ValueError("Invalid status")
        
        url = self._normalize_url(url)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if status == 'completed':
                cursor.execute('''
                    UPDATE scraped_urls 
                    SET status = 'completed', 
                        error_message = NULL,
                        file_path = ?,
                        last_successfully_scraped = CURRENT_TIMESTAMP
                    WHERE url = ?
                ''', (file_path, url))
            else:
                cursor.execute('''
                    UPDATE scraped_urls 
                    SET status = ?, 
                        error_message = ?
                    WHERE url = ?
                ''', (status, error_message, url))
            conn.commit()

    def get_next_pending_urls(self, limit: int = 10) -> List[str]:
        """Get the next batch of pending URLs to scrape, ordered by priority."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT url FROM scraped_urls 
                WHERE status = 'pending'
                ORDER BY priority ASC
                LIMIT ?
            ''', (limit,))
            return [row[0] for row in cursor.fetchall()]

    def get_url_info(self, url: str) -> dict:
        """Get the current status and metadata for a URL."""
        url = self._normalize_url(url)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT status, priority, error_message, file_path, 
                       last_successfully_scraped, created_at, updated_at
                FROM scraped_urls 
                WHERE url = ?
            ''', (url,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return {
                'status': row[0],
                'priority': row[1],
                'error_message': row[2],
                'file_path': row[3],
                'last_successfully_scraped': row[4],
                'created_at': row[5],
                'updated_at': row[6]
            }

    def _normalize_url(self, url: str) -> str:
        """Normalize URL format."""
        url = url.strip().rstrip('/').lower()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        parsed = urlparse(url)
        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            url += f"?{parsed.query}"
        return url

    def is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
  