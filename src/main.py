import os
from typing import Dict, List, Any, Tuple
from dotenv import load_dotenv
import psycopg
from nicegui import ui

load_dotenv()

DSN = os.getenv('DATABASE_URL')
ROLE = None
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


def login(as_role: str):
    """Входит в систему с указанной ролью"""
    global ROLE
    ROLE = as_role
    ui.notify(f'Вы вошли как {as_role}', color='positive')
    show_dashboard()


# Главный UI
with ui.column().classes('w-full') as login_page:
    with ui.card().classes('w-1/3 absolute-center'):
        ui.label('Система управления базой данных').classes('text-h4 text-center')
        ui.label('Выберите роль для входа:').classes('text-h6 mt-4')

        with ui.row().classes('justify-center gap-4 mt-4'):
            ui.button('Администратор', on_click=lambda: login('admin')).classes('bg-primary')
            ui.button('Пользователь', on_click=lambda: login('user')).classes('bg-secondary')

with ui.column().classes('w-full').bind_visibility_from(lambda: ROLE is not None) as dashboard_page:
    with ui.row().classes('justify-between w-full'):
        ui.label(f'Вы вошли как: {ROLE}').classes('text-h6')
        ui.button('Выйти', on_click=show_login).classes('bg-red')

    # Создаем вкладки
    with ui.tabs().classes('w-full') as tabs:
        entities = ['customers', 'orders', 'products', 'suppliers']
        tabs_dict = {entity: ui.tab(entity.capitalize()) for entity in entities}

    with ui.tab_panels(tabs, value=entities[0]).classes('w-full') as panels:
        for entity in entities:
            with ui.tab_panel(tabs_dict[entity]):
                with ui.row().classes('w-full gap-2'):
                    ui.button('Показать все', on_click=lambda e=entity: show_all(e)).classes('bg-blue')

                    # Кнопка только для админа
                    admin_button = ui.button('Счет строк', on_click=lambda e=entity: count_rows(e)).classes('bg-green')
                    admin_button.bind_visibility_from(lambda: ROLE == 'admin')

                # Карточка для админа
                admin_card = ui.card().classes('w-full')
                admin_card.bind_visibility_from(lambda: ROLE == 'admin')

                with admin_card:
                    ui.label('Выполнить произвольный запрос:').classes('text-bold')
                    query_input = ui.textarea(placeholder=f'SELECT * FROM {entity} WHERE...').classes('w-full')
                    ui.button('Выполнить', on_click=lambda e=entity, q=query_input: custom_query(e, q)).classes(
                        'bg-purple')

                ui.separator()
                # Создаем таблицу для результатов
                result_areas[entity] = ui.table(columns=[], rows=[]).classes('w-full')

# Инициализация
dashboard_page.visible = False

# Запускаем приложение
if __name__ in {'__main__', '__mp_main__'}:
    ui.run(title='Система управления базой данных', storage_secret='db_manager_secret')
