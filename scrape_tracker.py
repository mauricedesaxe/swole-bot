import sqlite3
from datetime import datetime
import os

class ScrapeTracker:
    def __init__(self, db_name: str = "scrape_tracker.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Initializes the database in the ./db directorys."""
        # make sure the db directory exists
        os.makedirs(os.path.dirname("./db"), exist_ok=True)

        # create the table
        with sqlite3.connect("./db/" + self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraped_urls (
                    url TEXT PRIMARY KEY,
                    last_scraped TIMESTAMP,
                    success BOOLEAN,
                    error_message TEXT,
                    file_path TEXT,
                    content_hash TEXT
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

    def get_url(self, url: str) -> tuple[bool, str | None]:
        with sqlite3.connect("./db/" + self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT success, file_path FROM scraped_urls WHERE url = ?', (url,))
            result = cursor.fetchone()
            return tuple(result) if result else (False, None)

    def get_all_urls(self) -> list[tuple[str, datetime, bool, str, str, str]]:
        with sqlite3.connect("./db/" + self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM scraped_urls')
            return cursor.fetchall()

    def clear_failed_urls(self) -> None:
        with sqlite3.connect("./db/" + self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM scraped_urls WHERE success = 0')
            conn.commit() 