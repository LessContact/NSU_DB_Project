import psycopg
from psycopg import OperationalError
from typing import Any, List, Tuple
from nicegui import ui
from config import DSN_ADMIN, DSN_HR


class DBManager:
    def __init__(self):
        self.conn = None

    def connect(self, role: str) -> bool:
        if role == 'admin':
            dsn = DSN_ADMIN
        elif role == 'hr':
            dsn = DSN_HR
        else:
            ui.notify("Invalid role specified", color='negative')
            return False

        try:
            if self.conn:
                self.conn.close()
            self.conn = psycopg.connect(dsn)
            ui.notify(f"Connected to database as {role}", color='positive')
            return True
        except OperationalError as e:
            ui.notify(f"OperationalError: {e}", color='negative', timeout=None, close_button=True)
            self.conn = None
            return False
        except Exception as e:
            ui.notify(f"Failed to connect as {role}: {e}", color='negative')
            self.conn = None
            return False

    def disconnect(self):
        try:
            if self.conn:
                self.conn.close()
                self.conn = None
                ui.notify("Disconnected from database", color='positive')
        except Exception as e:
            ui.notify(f"Failed to disconnect: {e}", color='negative')

    def execute_query(self, query: str) -> Tuple[List[str], List[Any]]:
        if not self.conn:
            ui.notify('No DB connection', color='negative')
            return [], []
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                try:
                    cols = [d[0] for d in cur.description]
                    data = cur.fetchall()
                    self.conn.commit()
                    return cols, data
                except psycopg.ProgrammingError as e:
                    self.conn.rollback()
                    ui.notify(f"DB error: {e}", color='negative')
                    return [], []
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            ui.notify(f"DB error: {e}", color='negative')
            return [], []


db_manager = DBManager()
