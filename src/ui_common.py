from nicegui import ui
from db import db_manager

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