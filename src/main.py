from nicegui import ui
from auth import User
import ui_login
import admin_dashboard
import hr_dashboard
from fastapi import Request

user = User()


def redirect_based_on_role():
    if not user.get_role():
        ui.navigate.to('/login')
    elif user.get_role() == 'admin':
        ui.navigate.to('/admin')
    elif user.get_role() == 'hr':
        ui.navigate.to('/hr')


@ui.page('/')
def index_page():
    ui.navigate.to('/login')


@ui.page('/login')
def login_page():
    def handle_login(role: str):
        if user.change_role(role):
            ui.notify(f'Вход выполнен как {role}', color='positive')
            redirect_based_on_role()
        else:
            ui.notify('Ошибка подключения к базе', color='negative')

    ui_login.build_login(handle_login)


@ui.page('/admin')
def admin_page():
    if user.get_role() != 'admin':
        redirect_based_on_role()
        return

    async def handle_logout():
        user.logout()
        ui.navigate.to('/login')

    admin_dashboard.build_dashboard(user, handle_logout)


@ui.page('/hr')
def hr_page():
    if user.get_role() != 'hr':
        redirect_based_on_role()
        return

    async def handle_logout():
        user.logout()
        ui.navigate.to('/login')

    hr_dashboard.build_dashboard(user, handle_logout)


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(host='localhost', title='Система управления базой данных', favicon='💽', dark=None,
           reload=False, reconnect_timeout=10.0, uvicorn_logging_level='warning')