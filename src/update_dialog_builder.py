from typing import Callable, Dict
from nicegui import ui
from psycopg import sql
from src.utils import create_date_input_field

update_dialog_builders: dict[str, Callable] = {}

def register_dialog(table_name: str):
    def decorator(fn: Callable):
        update_dialog_builders[table_name] = fn
        return fn
    return decorator



