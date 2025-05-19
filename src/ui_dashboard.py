from nicegui import ui
from db import db_manager


def build_dashboard(user, on_logout):
    entities = ['customers', 'orders', 'products', 'suppliers']
    result_areas = {}

    with ui.column().classes('full-width') as dashboard_page:
        with ui.row().classes('full-width items-center q-pa-md'):
            ui.label('').classes('text-h6').bind_text_from(user, 'role', lambda x: 'Вы вошли как ' + x)
            ui.space().classes('grow')
            ui.button('Выйти', on_click=on_logout).classes('q-btn-negative')

        labels = [ent.capitalize() for ent in entities]
        with ui.tabs() as tabs:
            for lbl in labels:
                ui.tab(lbl)

        with ui.tab_panels(tabs, value=labels[0]).classes('full-width') as panels:
            for lbl in labels:
                with ui.tab_panel(lbl):
                    with ui.row().classes('full-width q-gutter-sm'):
                        ui.button('Показать все', on_click=lambda e=lbl: show_all(e, result_areas)).classes(
                            'q-btn-primary')
                        admin_button = ui.button('Счет строк',
                                                 on_click=lambda e=lbl: count_rows(e, result_areas)).classes(
                            'q-btn-positive')
                        admin_button.bind_visibility_from(lambda: user.get_role() == 'admin')

                    admin_card = ui.card().classes('full-width')
                    admin_card.bind_visibility_from(lambda: user.get_role() == 'admin')

                    with admin_card:
                        ui.label('Выполнить произвольный запрос:').classes('text-weight-bold')
                        query_input = ui.textarea(placeholder=f'SELECT * FROM {lbl} WHERE...').classes('full-width')
                        ui.button('Выполнить',
                                  on_click=lambda e=lbl, q=query_input: custom_query(e, q, result_areas)).classes(
                            'q-btn-purple')

                    ui.separator()
                    result_areas[lbl] = ui.table(columns=[], rows=[]).classes('full-width')
    return dashboard_page


def display_result(entity, cols, data, areas):
    if not data:
        ui.notify('No data', color='warning')
    cols_def = [{'name': c, 'label': c, 'field': c} for c in cols]
    rows = [dict(zip(cols, row)) for row in data]
    table = areas[entity]
    table.update_columns(cols_def)
    table.update_rows(rows)


def show_all(entity, areas):
    cols, data = db_manager.execute_query(f"SELECT * FROM {entity} LIMIT 100")
    display_result(entity, cols, data, areas)


def count_rows(entity, areas):
    cols, data = db_manager.execute_query(f"SELECT COUNT(*) AS count FROM {entity}")
    display_result(entity, cols, data, areas)


def custom_query(entity, query_input, areas):
    sql = query_input.value.strip()
    if not sql:
        ui.notify('Empty query', color='negative')
        return
    cols, data = db_manager.execute_query(sql)
    display_result(entity, cols, data, areas)
