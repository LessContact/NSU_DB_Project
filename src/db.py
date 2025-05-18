import psycopg
from typing import Any, List, Tuple
from nicegui import ui
from config import DSN_ADMIN, DSN_HR


class DBManager:
    def __init__(self):
        self.conn = None

    def connect(self, role: str):
        if role == 'admin':
            dsn = DSN_ADMIN
        elif role == 'hr':
            dsn = DSN_HR
        else:
            ui.notify("Invalid role specified", color='negative')
            return

        try:
            if self.conn:
                self.conn.close()
            self.conn = psycopg.connect(dsn)
            ui.notify(f"Connected to database as {role}", color='positive')
        except Exception as e:
            ui.notify(f"Failed to connect as {role}: {e}", color='negative')

    def disconnect(self):
        try:
            if self.conn:
                self.conn.close()
                self.conn = None
                ui.notify("Disconnected from database", color='positive')
        except Exception as e:
            ui.notify(f"Failed to disconnect: {e}", color='negative')

    def execute_query(self, query: str) -> Tuple[List[str], List[Any]]:
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                try:
                    cols = [d[0] for d in cur.description]
                    data = cur.fetchall()
                    return cols, data
                except psycopg.ProgrammingError as e:
                    ui.notify(f"DB error: {e}", color='negative')
                    return [], []
        except Exception as e:
            ui.notify(f"DB error: {e}", color='negative')
            return [], []

db_manager = DBManager()
