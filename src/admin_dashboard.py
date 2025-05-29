from nicegui import ui

from add_dialog_builder import add_dialog_builders
from delete_dialog_builder import delete_dialog_builders
from get_dialog_builder import get_dialog_builders
from update_dialog_builder import update_dialog_builders
from db import db_manager
from generic_dialog_builders import build_generic_add_dialog, build_generic_delete_dialog, build_generic_get_dialog, \
    build_generic_update_dialog
from src.update_dialog_builder import update_dialog_builders
from ui_common import show_all, count_rows, custom_query, get_user_tables, get_all_views, check_user_privileges


def build_dashboard(user, on_logout):
    entities = get_user_tables(db_manager.conn)
    result_areas = {}

    with ui.column().classes('full-width') as dashboard_page:
        with ui.row().classes('full-width items-center q-pb-sm'):
            ui.label('Вы вошли как admin').classes('text-h6')
            ui.space().classes('grow')
            ui.button('Выйти', on_click=on_logout).classes('q-btn-negative')

        labels = entities
        with ui.row().classes('full-width full-height'):
            with ui.column().classes('w-1/4 h-full').style('max-width: 200px;'):
                with ui.tabs().props('vertical').classes('full-width center') as tabs:
                    ui.tab('summaries')
                    for lbl in labels:
                        ui.tab(lbl)
            with ui.column().style('flex: 1;'):
                with ui.tab_panels(tabs, value=labels[0]).props('vertical').classes('full-width center') as panels:
                    #create summary tab
                    with ui.tab_panel('summaries'):
                        with ui.row().classes('full-width q-gutter-sm'):
                            for view in get_all_views(db_manager.conn):
                                view_builder = get_dialog_builders.get(view, build_generic_get_dialog)
                                view_dlg = view_builder(db_manager.conn, view, result_areas)
                                ui.button(f'Filter from {view}', on_click=view_dlg.open)
                                ui.separator()
                                result_areas[view] = ui.table(columns=[], rows=[]).classes('full-width')

                    for lbl in labels:
                        with ui.tab_panel(lbl):
                            with ui.row().classes('full-width q-gutter-sm'):
                                # Check user privileges
                                privileges = check_user_privileges(db_manager.conn, lbl)
                                # Buttons go HEREEEEEE
                                # Add button with dialogggg
                                if privileges.get('INSERT', False):
                                    add_builder = add_dialog_builders.get(lbl, build_generic_add_dialog)
                                    add_dlg = add_builder(db_manager.conn, lbl)
                                    ui.button(f'Add to {lbl}', on_click=add_dlg.open)
                                if privileges.get('DELETE', False):
                                    del_builder = delete_dialog_builders.get(lbl, build_generic_delete_dialog)
                                    del_dlg = del_builder(db_manager.conn, lbl)
                                    ui.button(f'Delete from {lbl}', on_click=del_dlg.open)

                                get_builder = get_dialog_builders.get(lbl, build_generic_get_dialog)
                                get_dlg = get_builder(db_manager.conn, lbl, result_areas)
                                ui.button(f'Filter from {lbl}', on_click=get_dlg.open)
                                if privileges.get('UPDATE', False):
                                    upd_builder = update_dialog_builders.get(lbl, build_generic_update_dialog)
                                    upd_dlg = upd_builder(db_manager.conn, lbl)
                                    ui.button(f'Update {lbl}', on_click=upd_dlg.open)

                            with ui.card().classes('full-width'):
                                ui.label('Выполнить произвольный запрос:').classes('text-weight-bold')
                                query_input = ui.textarea(placeholder=f'SELECT * FROM {lbl} WHERE...').classes('full-width')
                                ui.button('Выполнить', on_click=lambda e=lbl, q=query_input: custom_query(e, q, result_areas)).classes('q-btn-purple')

                            ui.separator()
                            result_areas[lbl] = ui.table(columns=[], rows=[]).classes('full-width')
    return dashboard_page
