from nicegui import ui


def build_login(on_login) -> any:
    with ui.column().classes('w-full').style("position: absolute; top: 33.3%; left: 33.3%;") as login_page:
        with ui.card(align_items='center').classes('items-center w-1/3 flex-col p-4 gap-4'):
            ui.label('Система управления базой данных').classes('text-h4 text-center')
            ui.label('Выберите роль для входа.').classes('text-h6 text-center')

            with ui.row().classes('flex justify-center items-center gap-4 w-full'):
                ui.button('Администратор', on_click=lambda: on_login('admin')).classes('bg-primary')
                ui.button('Отдел кадров', on_click=lambda: on_login('hr')).classes('bg-secondary')
    return login_page
