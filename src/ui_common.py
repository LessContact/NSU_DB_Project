from nicegui import ui
from db import db_manager
import psycopg
from src.config import DSN_ADMIN, DSN_HR

def get_all_views(conn) -> list[str]:
    """
    Return a list of all views in the database.

    If exclude_system_schemas is True, filters out pg_catalog and information_schema.
    """
    sql = """
          SELECT table_schema, table_name
          FROM information_schema.views
          WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
          ORDER BY table_schema, table_name; \
          """
    with conn.cursor() as cur:
        cur.execute(sql)
        return [f"{name}" for schema, name in cur.fetchall()]


def get_user_tables(conn):
    try:
        """Return all public tables the current user can SELECT."""
        query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                  AND has_table_privilege(table_schema || '.' || table_name, 'SELECT')
                ORDER BY table_name;
                """
        with conn.cursor() as cur:
            cur.execute(query)
            return [row[0] for row in cur.fetchall()]
    except Exception as e:
        ui.notify(f"Failed to populate entities", color='negative')
        return None


def check_user_privileges(conn, table_name):
    """
    Проверяет привилегии текущего пользователя для таблицы.
    Возвращает словарь с ключами 'INSERT', 'UPDATE', 'DELETE' и булевыми значениями.
    """
    privileges = {}
    operations = ['INSERT', 'UPDATE', 'DELETE']

    try:
        with conn.cursor() as cur:
            for operation in operations:
                query = f"""
                SELECT has_table_privilege(current_user, 'public.{table_name}', '{operation}')
                """
                cur.execute(query)
                result = cur.fetchone()[0]
                privileges[operation] = result
        return privileges
    except Exception as e:
        ui.notify(f"Ошибка проверки привилегий: {str(e)}", color='negative')
        return {op: False for op in operations}


def display_result(entity, cols, data, areas):
    if not data:
        ui.notify('No data', color='warning')
        return

    cols_def = [{'name': c, 'label': c, 'field': c} for c in cols]
    rows = [dict(zip(cols, row)) for row in data]

    areas[entity].columns = cols_def
    areas[entity].rows = rows

def show_all(entity, areas):
    cols, data = db_manager.execute_query(f"SELECT * FROM {entity} LIMIT 100;")
    display_result(entity, cols, data, areas)

def count_rows(entity, areas):
    cols, data = db_manager.execute_query(f"SELECT COUNT(*) AS count FROM {entity};")
    display_result(entity, cols, data, areas)

def custom_query(entity, query_input, areas):
    sql = query_input.value.strip()
    if not sql:
        ui.notify('Empty query', color='negative')
        return
    cols, data = db_manager.execute_query(sql)
    display_result(entity, cols, data, areas)
