from typing import Callable
from nicegui import ui
from psycopg import sql, OperationalError, IsolationLevel

from src.utils import create_date_input_field

summary_dialog_builders: dict[str, Callable] = {}

def register_dialog(table_name: str):
    def decorator(fn: Callable):
        summary_dialog_builders[table_name] = fn
        return fn
    return decorator

#TODO: FIX THESE SUMMARIES THE DONT SEEM TO WORK
