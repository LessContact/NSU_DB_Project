from nicegui import ui
from auth import User


def build_login(on_login) -> any:
    with ui.element('div').classes('w-full absolute-center') as login_page:
        with ui.card(align_items='center').classes('items-center w-1/3 flex-col p-4 gap-4'):
            ui.label('Система управления базой данных').classes('text-h4 text-center')
            ui.label('Выберите роль для входа.').classes('text-h6 text-center')

            with ui.row().classes('flex justify-center items-center gap-4 w-full'):
                ui.button('Администратор', on_click=lambda: on_login('admin')).classes('bg-primary')
                ui.button('Пользователь', on_click=lambda: on_login('user')).classes('bg-secondary')
    return login_page
