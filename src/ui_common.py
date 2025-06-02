from nicegui import ui
from db import db_manager

def get_all_views(conn) -> list[str]:
    """
    Return a list of all views in the database.
    """
    sql = """
          SELECT table_schema, table_name
          FROM information_schema.views
          WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
          ORDER BY table_schema, table_name;
          """
    with conn.cursor() as cur:
        cur.execute(sql)
        return [f"{name}" for schema, name in cur.fetchall()]


def get_all_functions(conn) -> list[str]:
    """
    Return a list of all functions in the database.
    """
    sql = """
        SELECT
        n.nspname AS schema,
        p.proname AS function_name
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE
        n.nspname NOT IN ('pg_catalog', 'information_schema')
        -- Keep only normal functions
        AND p.prokind = 'f'
        -- Exclude trigger functions
        AND pg_catalog.pg_get_function_result(p.oid) != 'trigger'
        ORDER BY function_name;
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

    cols_def = [{'name': c, 'label': c.replace('_', ' ').title(), 'field': c} for c in cols]

    prepared_rows = []
    for row_tuple in data:
        row_dict = {}
        for i, col_name in enumerate(cols):
            cell_value = row_tuple[i]
            if isinstance(cell_value, list):
                row_dict[col_name] = ', '.join(map(str, cell_value))
            else:
                row_dict[col_name] = cell_value
        prepared_rows.append(row_dict)

    target_display_element = areas.get(entity)

    if target_display_element:
        target_display_element.columns = cols_def
        target_display_element.rows = prepared_rows
        target_display_element.update()
    else:
        ui.notify(f"Error: UI element for '{entity}' not found in result_areas.", color='negative')


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
