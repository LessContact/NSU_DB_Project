from nicegui import ui, app
from auth import User
import ui_login
import admin_dashboard
import hr_dashboard
from db import db_manager


user = User()


def shutdown():
    db_manager.disconnect()
    print('Соединение с базой данных закрыто')


def disconnect():
    user.role = ''


app.on_shutdown(shutdown)
app.on_disconnect(disconnect)

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
    def handle_login(username: str, password: str, role: str):
        if authenticate_user(username, password, role):
            if user.change_role(role):
                ui.notify(f'Добро пожаловать, {username}!', color='positive')
                redirect_based_on_role()
            else:
                ui.notify('Ошибка подключения к базе', color='negative')
        else:
            ui.notify('Неверные учетные данные', color='negative')

    ui_login.build_login(handle_login)


def authenticate_user(username: str, password: str, role: str) -> bool:
    """
    Things is should but won't do:
    1. Hash passwords
    2. Use a proper database
    3. Implement proper security measures
    """
    valid_credentials = {
        'admin': {'admin': 'admin', 'admin1': '1'},
        'hr': {'hr': 'hr', 'hr1': '1'}
    }

    return (role in valid_credentials and
            username in valid_credentials[role] and
            valid_credentials[role][username] == password)


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
    ui.run(host='localhost', title='Информационная система авиастроительного предприятия ', favicon='💽', dark=None,
           reload=False, reconnect_timeout=10.0, uvicorn_logging_level='warning')
