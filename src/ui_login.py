from nicegui import ui


def build_login(on_login) -> any:
    def handle_login_click():
        if not username.value or not password.value:
            ui.notify('Пожалуйста, заполните все поля', color='orange')
            return

        on_login(username.value, password.value, role_select.value)

    with ui.column().classes('w-full h-screen flex justify-center items-center') as login_page:
        with ui.card().classes('w-96 p-6'):
            with ui.column().classes('w-full gap-4'):
                ui.label('Информационная система авиастроительного предприятия ').classes('text-h4 text-center mb-4')
                ui.label('Войдите в систему').classes('text-h6 text-center mb-6')
                username = ui.input(label='Имя пользователя', placeholder='admin').classes('w-full')
                password = ui.input(label='Пароль', placeholder='admin', password=True, password_toggle_button=True).classes('w-full')
                role_select = ui.select(['admin', 'hr'], label='Роль', value='admin').classes('w-full')
                login_button = ui.button('Войти').classes('bg-primary w-full')
                username.classes('mb-2')
                password.classes('mb-2')
                role_select.classes('mb-4')

                login_button.on_click(handle_login_click)

                username.on('keydown.enter', handle_login_click)
                password.on('keydown.enter', handle_login_click)

    return login_page
