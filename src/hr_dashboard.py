from nicegui import ui
from add_dialog_builder import add_dialog_builders
from delete_dialog_builder import delete_dialog_builders
from get_dialog_builder import get_dialog_builders
from update_dialog_builder import update_dialog_builders
from db import db_manager
from generic_dialog_builders import build_generic_add_dialog, build_generic_delete_dialog, build_generic_get_dialog, \
    build_generic_update_dialog
from ui_common import show_all, count_rows, custom_query, get_user_tables

def build_dashboard(user, on_logout):
    entities = get_user_tables(user.role)
    result_areas = {}

    with ui.column().classes('full-width') as dashboard_page:
        with ui.row().classes('full-width items-center q-pb-sm'):
            ui.label('').classes('text-h6').bind_text_from(user, 'role', lambda x: 'Вы вошли как ' + x)
            ui.space().classes('grow')
            ui.button('Выйти', on_click=on_logout).classes('q-btn-negative')

        labels = entities
        with ui.row().classes('full-width full-height'):
            with ui.column().classes('w-1/4 h-full').style('max-width: 200px;'):
                with ui.tabs().props('vertical').classes('full-width center') as tabs:
                    for lbl in labels:
                        ui.tab(lbl)
            with ui.column().style('flex: 1;'):
                with ui.tab_panels(tabs, value=labels[0]).props('vertical').classes('full-width center') as panels:
                    for lbl in labels:
                        with ui.tab_panel(lbl):
                            with ui.row().classes('full-width q-gutter-sm'):
                                add_builder = add_dialog_builders.get(lbl, build_generic_add_dialog)
                                add_dlg = add_builder(db_manager.conn, lbl)
                                ui.button(f'Add to {lbl}', on_click=add_dlg.open)
                                del_builder = delete_dialog_builders.get(lbl, build_generic_delete_dialog)
                                del_dlg = del_builder(db_manager.conn, lbl)
                                ui.button(f'Delete from {lbl}', on_click=del_dlg.open)
                                get_builder = get_dialog_builders.get(lbl, build_generic_get_dialog)
                                get_dlg = get_builder(db_manager.conn, lbl, result_areas)
                                ui.button(f'Filter from {lbl}', on_click=get_dlg.open)
                                upd_builder = update_dialog_builders.get(lbl, build_generic_update_dialog)
                                upd_dlg = upd_builder(db_manager.conn, lbl)
                                ui.button(f'Update {lbl}', on_click=upd_dlg.open)

                            ui.separator()
                            result_areas[lbl] = ui.table(columns=[], rows=[]).classes('full-width')
    return dashboard_page
