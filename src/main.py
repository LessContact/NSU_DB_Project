import os
from typing import Dict, List, Any, Tuple
from dotenv import load_dotenv
import psycopg
from nicegui import ui

load_dotenv()

DSN = os.getenv('DATABASE_URL')
result_areas = {}


def execute_query(query: str) -> Tuple[List[str], List[Any]]:
    """Выполняет SQL-запрос и возвращает имена столбцов и данные"""
    try:
        with psycopg.connect(DSN) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                try:
                    column_names = [desc[0] for desc in cur.description]
                    data = cur.fetchall()
                    return column_names, data
                except psycopg.ProgrammingError:
                    return [], []
    except Exception as e:
        ui.notify(f'Ошибка подключения к базе данных: {str(e)}', color='negative')
        return [], []


def display_result(entity: str, column_names: List[str], data: List[Any]) -> None:
    """Отображает результаты запроса в соответствующей таблице"""
    if not data:
        ui.notify('Нет данных для отображения', color='warning')
        result_areas[entity].update_rows([])
        result_areas[entity].update_columns([{'name': col, 'label': col, 'field': col} for col in column_names])
        return

    columns = [{'name': col, 'label': col, 'field': col} for col in column_names]
    rows = [dict(zip(column_names, row)) for row in data]
    result_areas[entity].update_columns(columns)
    result_areas[entity].update_rows(rows)


def show_all(entity: str) -> None:
    """Показывает все записи для указанной сущности"""
    query = f'SELECT * FROM {entity} LIMIT 100'
    column_names, data = execute_query(query)
    display_result(entity, column_names, data)


def count_rows(entity: str) -> None:
    """Подсчитывает количество строк в таблице"""
    query = f'SELECT COUNT(*) as Количество FROM {entity}'
    column_names, data = execute_query(query)
    display_result(entity, column_names, data)


def custom_query(entity: str, query_input) -> None:
    """Выполняет пользовательский запрос"""
    query_text = query_input.value
    if not query_text.strip():
        ui.notify('Запрос не может быть пустым', color='negative')
        return
    column_names, data = execute_query(query_text)
    display_result(entity, column_names, data)


def show_login():
    """Переключается на экран логина"""
    login_page.visible = True
    dashboard_page.visible = False


def show_dashboard():
    """Переключается на экран дашборда"""
    login_page.visible = False
    dashboard_page.visible = True


class User:
    role: str
    def __init__(self, role: str):
        self.role = role

    def __str__(self):
        return self.role

    def get_role(self):
        return self.role

    def change_role(self, as_role: str):
        """Входит в систему с указанной ролью"""
        self.role = as_role
        ui.notify(f'Вы вошли как {self.role}', color='positive')
        show_dashboard()

user = User('')

with ui.element('div').classes('w-full absolute-center') as login_page:
    with ui.card(align_items='center').classes('items-center w-1/3 flex-col p-4 gap-4'):
        ui.label('Система управления базой данных').classes('text-h4 text-center')
        ui.label('Выберите роль для входа.').classes('text-h6 text-center')

        with ui.row().classes('flex justify-center items-center gap-4 w-full'):
            ui.button('Администратор', on_click=lambda: user.change_role('admin')).classes('bg-primary')
            ui.button('Пользователь', on_click=lambda: user.change_role('user')).classes('bg-secondary')

with ui.column().classes('full-width').bind_visibility_from(lambda: user.get_role() != '') as dashboard_page:
    with ui.row().classes('full-width items-center q-pa-md'):
        ui.label(f'Вы вошли как: {user.get_role()}').classes('text-h6')

        ui.space().classes('grow')

        ui.button('Выйти', on_click=show_login).classes('q-btn-negative')

    with ui.row().classes('full-width justify-center q-mb-md'):
        with ui.tabs().classes('') as tabs:
            entities = ['customers', 'orders', 'products', 'suppliers']
            tabs_dict = {entity: ui.tab(entity.capitalize()).classes('q-mx-xs') for entity in entities}

    with ui.tab_panels(tabs, value=entities[0]).classes('full-width') as panels:
        for entity in entities:
            with ui.tab_panel(tabs_dict[entity]):
                with ui.row().classes('full-width q-gutter-sm'):
                    ui.button('Показать все', on_click=lambda e=entity: show_all(e)).classes('q-btn-primary')
                    admin_button = ui.button('Счет строк', on_click=lambda e=entity: count_rows(e)).classes('q-btn-positive')
                    admin_button.bind_visibility_from(lambda: user.get_role() == 'admin')

                admin_card = ui.card().classes('full-width')
                admin_card.bind_visibility_from(lambda: user.get_role() == 'admin')

                with admin_card:
                    ui.label('Выполнить произвольный запрос:').classes('text-weight-bold')
                    query_input = ui.textarea(placeholder=f'SELECT * FROM {entity} WHERE...').classes('full-width')
                    ui.button('Выполнить', on_click=lambda e=entity, q=query_input: custom_query(e, q)).classes('q-btn-purple')

                ui.separator()
                result_areas[entity] = ui.table(columns=[], rows=[]).classes('full-width')

# Инициализация
dashboard_page.visible = False

# Запускаем приложение
if __name__ in {'__main__', '__mp_main__'}:
    ui.run(host='localhost', title='Система управления базой данных', favicon='💽', dark=None, uvicorn_logging_level='warning')
