from nicegui import ui
from auth import User
import ui_login, ui_dashboard

user = User()

def show_login():
    login_page.visible = True
    dashboard_page.visible = False

def show_dashboard():
    login_page.visible = False
    dashboard_page.visible = True

login_page = ui_login.build_login(on_login=lambda role: (user.change_role(role), show_dashboard()))
dashboard_page = ui_dashboard.build_dashboard(user, on_logout=lambda: (user.logout(), show_login()))

dashboard_page.visible = False

if __name__ in {'__main__', '__mp_main__'}:
    ui.run(host='localhost', title='Система управления базой данных', favicon='💽', dark=None, uvicorn_logging_level='warning')
