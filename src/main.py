from nicegui import ui
from auth import User
import ui_login
import admin_dashboard, hr_dashboard

user = User()
current_dashboard = None


def on_logout():
    user.logout()
    if current_dashboard:
        current_dashboard.visible = False
    show_login()


def on_login(role: str):
    if user.change_role(role):
        show_dashboard(role)
        ui.notify(f'Logged in as {role}', color='positive')
    else:
        ui.notify('Could not login; check database credentials/connection', color='negative')
        show_login()


def show_login():
    login_page.visible = True
    if current_dashboard:
        current_dashboard.visible = False


def show_dashboard(role: str):
    global current_dashboard
    login_page.visible = False

    # Скрыть текущий дашборд, если он существует
    if current_dashboard:
        current_dashboard.visible = False

    # Выбрать соответствующий дашборд согласно роли
    if role == 'admin':
        admin_dashboard.visible = True
        current_dashboard = admin_dashboard
    elif role == 'hr':
        hr_dashboard.visible = True
        current_dashboard = hr_dashboard


login_page = ui_login.build_login(on_login)

# Создаем отдельные дашборды для разных ролей
admin_dashboard = admin_dashboard.build_dashboard(user, on_logout)
hr_dashboard = hr_dashboard.build_dashboard(user, on_logout)

admin_dashboard.visible = False
hr_dashboard.visible = False

if __name__ in {'__main__', '__mp_main__'}:
    ui.run(host='localhost', title='Система управления базой данных', favicon='💽', dark=None,
           reload=False, reconnect_timeout=10.0, uvicorn_logging_level='warning')