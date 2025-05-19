from nicegui import ui
from auth import User
import ui_login, ui_dashboard

user = User()


def on_logout():
    user.logout()
    show_login()


def on_login(role : str):
    if user.change_role(role):
        show_dashboard()
        ui.notify(f'Logged in as {role}', color='positive')
    else:
        ui.notify('Could not login; check database credentials/connection', color='negative')
        show_login()

def show_login():
    login_page.visible = True
    dashboard_page.visible = False


def show_dashboard():
    login_page.visible = False
    dashboard_page.visible = True


login_page = ui_login.build_login(on_login)
dashboard_page = ui_dashboard.build_dashboard(user, on_logout)

dashboard_page.visible = False

if __name__ in {'__main__', '__mp_main__'}:
    ui.run(host='localhost', title='Система управления базой данных', favicon='💽', dark=None,
           reload=False, reconnect_timeout=10.0, uvicorn_logging_level='warning')
