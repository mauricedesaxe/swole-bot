import sqlite3
from datetime import datetime
import os
from typing import Optional, Tuple, List

class ScrapeTracker:
    def __init__(self, db_name: str = "scrape_tracker.db"):
        self.db_name = db_name
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

    def add_url(self, url: str, success: bool, file_path: str = None, error_message: str = None) -> None:
        with sqlite3.connect("./db/" + self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO scraped_urls 
                (url, last_scraped, success, error_message, file_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (url, datetime.now(), success, error_message, file_path))
            conn.commit()

    def get_url(self, url: str) -> Tuple[bool, Optional[str]]:
        with sqlite3.connect("./db/" + self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT success, file_path FROM scraped_urls WHERE url = ?', (url,))
            result = cursor.fetchone()
            return tuple(result) if result else (False, None)

    def get_all_urls(self) -> List[Tuple[str, datetime, bool, str, str, str]]:
        with sqlite3.connect("./db/" + self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM scraped_urls')
            return cursor.fetchall()

    def clear_failed_urls(self) -> None:
        with sqlite3.connect("./db/" + self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM scraped_urls WHERE success = 0')
            conn.commit() 