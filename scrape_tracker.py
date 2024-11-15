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
                    last_scraped TIMESTAMP,
                    success BOOLEAN,
                    error_message TEXT,
                    file_path TEXT
                )
            ''')
            conn.commit()

    def add_scraped_url(self, url: str, success: bool, file_path: str = None, error_message: str = None) -> None:
        if not self.is_valid_url(url):
            raise ValueError("Invalid URL format")
        if file_path and not os.path.exists(file_path):
            raise ValueError("File path does not exist")
        
        # Normalize URL by removing trailing slashes, converting to lowercase, and ensuring consistent scheme
        url = url.strip().rstrip('/').lower()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        parsed = urlparse(url)
        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            url += f"?{parsed.query}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO scraped_urls 
                (url, last_scraped, success, error_message, file_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (url, datetime.now(timezone.utc), success, error_message, file_path))
            conn.commit()

    def get_scraped_url(self, url: str) -> Tuple[bool, Optional[str]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT success, file_path FROM scraped_urls WHERE url = ?', (url,))
            result = cursor.fetchone()
            return tuple(result) if result else (False, None)

    def get_all_scraped_urls(self) -> List[Tuple[str, datetime, bool, str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM scraped_urls')
            return cursor.fetchall()

    def clear_failed_scraped_urls(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM scraped_urls WHERE success = 0')
            conn.commit() 

    def is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
  