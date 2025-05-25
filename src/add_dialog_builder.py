from typing import Callable
from nicegui import ui
from psycopg import sql

from src.utils import create_date_input_field

dialog_builders: dict[str, Callable] = {}

def register_dialog(table_name: str):
    def decorator(fn: Callable):
        dialog_builders[table_name] = fn
        return fn
    return decorator


@register_dialog('employees')
def build_employees_dialog(conn, table_name):
    with ui.dialog() as dialog, ui.card():
        ui.label('Add Employee').classes('text-h6')
        name = ui.input(label='Full Name')
        hire_date = create_date_input_field("Hire Date")
        leave_date = create_date_input_field("Leave Date")
        worker_type = ui.select(['Рабочий','Инженер','Тестировщик'], label='Employee Type')
        experience = ui.number(label='Experience (years)')
        grade = ui.select(['Рабочий 3 разряда','Рабочий 4 разряда','Рабочий 5 разряда','Рабочий 6 разряда','Бригадир','Инженер','Начальник цеха','Тестировщик'], label='Employee Type')
        def on_submit():
            name_val = name.value
            hire_val = hire_date.value
            leave_val = leave_date.value or None
            wt_name = worker_type.value
            exp_val = experience.value
            grade_name = grade.value

            table = sql.Identifier(table_name)
            cols = [
                "full_name", "hire_date", "leave_date",
                "worker_type", "experience", "grade_id"
            ]
            idents = [sql.Identifier(c) for c in cols]

            #    Build placeholders and sub‐SELECTs for the two foreign keys
            #    - Placeholder() → %s
            #    - Sub‐select for wt_id: (SELECT id FROM worker_types WHERE name = %s)
            #    - Sub‐select for g_id: (SELECT id FROM grades       WHERE grade_name = %s)
            placeholders = [
                sql.Placeholder(),  # name
                sql.Placeholder(),  # hire_date
                sql.Placeholder(),  # leave_date
                sql.SQL("(SELECT tp_id FROM worker_types WHERE name = {})")
                .format(sql.Placeholder()),  # wt_id
                sql.Placeholder(),  # experience
                sql.SQL("(SELECT g_id FROM grades WHERE grade_title = {})")
                .format(sql.Placeholder()),  # g_id
            ]

            query = sql.SQL("INSERT INTO {tbl} ({fields}) VALUES ({values})").format(
                tbl=table,
                fields=sql.SQL(", ").join(idents),
                values=sql.SQL(", ").join(placeholders),
            )

            # Execute with a flat list of parameters in the exact order of placeholders
            params = [
                name_val,
                hire_val,
                leave_val,
                wt_name,  # for worker_types.name
                exp_val,
                grade_name,  # for grades.grade_name
            ]
            try:
                conn.execute(query, params)
                conn.commit()
            except Exception as e:
                ui.notify(f'Error inserting employee: {e}', color='negative')
                conn.rollback()
                return
            ui.notify('Employee created')
            dialog.close()

        ui.button('Create', on_click=on_submit).classes('q-btn-primary')
    return dialog


