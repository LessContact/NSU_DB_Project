from nicegui import ui
from ui_common import show_all, count_rows, custom_query

def build_dashboard(user, on_logout):
    entities = ['Products', 'Employees', 'Assembly', 'Workshops']
    result_areas = {}

    with ui.column().classes('full-width') as dashboard_page:
        with ui.row().classes('full-width items-center q-pa-md'):
            ui.label('').classes('text-h6').bind_text_from(user, 'role', lambda x: 'Вы вошли как ' + x)
            ui.space().classes('grow')
            ui.button('Выйти', on_click=on_logout).classes('q-btn-negative')

        labels = [ent.capitalize() for ent in entities]
        with ui.tabs().classes('full-width center') as tabs:
            for lbl in labels:
                ui.tab(lbl)

        with ui.tab_panels(tabs, value=labels[0]).classes('full-width center') as panels:
            for lbl in labels:
                with ui.tab_panel(lbl):
                    with ui.row().classes('full-width q-gutter-sm'):
                        ui.button('Показать все', on_click=lambda e=lbl: show_all(e, result_areas)).classes('q-btn-primary')
                        ui.button('Счет строк', on_click=lambda e=lbl: count_rows(e, result_areas)).classes('q-btn-positive')

                    with ui.card().classes('full-width'):
                        ui.label('Выполнить произвольный запрос:').classes('text-weight-bold')
                        query_input = ui.textarea(placeholder=f'SELECT * FROM {lbl} WHERE...').classes('full-width')
                        ui.button('Выполнить', on_click=lambda e=lbl, q=query_input: custom_query(e, q, result_areas)).classes('q-btn-purple')

                    ui.separator()
                    result_areas[lbl] = ui.table(columns=[], rows=[]).classes('full-width')
    return dashboard_page