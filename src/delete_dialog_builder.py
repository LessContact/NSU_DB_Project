from typing import Callable, Dict
from nicegui import ui
from psycopg import sql
from src.utils import create_date_input_field

delete_dialog_builders: dict[str, Callable] = {}

def register_dialog(table_name: str):
    def decorator(fn: Callable):
        delete_dialog_builders[table_name] = fn
        return fn
    return decorator


@register_dialog('employees')
def build_employees_remove_dialog(conn, table_name):
    with ui.dialog() as dialog, ui.card().classes('w-1/2'):
        ui.label('Remove Employee').classes('text-h6')

        employee_id = ui.number(label='Employee ID').classes('w-full')
        info_card = ui.card().classes('q-mt-md w-full')
        with info_card:
            employee_name_display = ui.label('Select an employee to see details').classes('text-subtitle1')
            employee_type_display = ui.label('')

        # Status and action area
        action_area = ui.column().classes('q-mt-md w-full')

        def fetch_employee_info():
            emp_id = employee_id.value
            if not emp_id:
                ui.notify('Please enter an employee ID', color='warning')
                return

            action_area.clear()

            try:
                with conn.cursor() as cur:
                    query = '''
                        SELECT e.w_id, e.full_name, wt.name as worker_type
                        FROM employees e
                        JOIN worker_types wt ON e.worker_type = wt.tp_id
                        WHERE e.w_id = %s
                    '''
                    cur.execute(query, [emp_id])
                    result = cur.fetchone()

                    if result:
                        employee_name_display.text = f"Name: {result[1]}"
                        employee_type_display.text = f"Employee Type: {result[2]}"

                        with action_area:
                            ui.label(f"Are you sure you want to remove {result[1]}?").classes(
                                'text-subtitle1 text-negative')
                            with ui.row().classes('q-mt-md justify-end'):
                                ui.button('Cancel', on_click=dialog.close).classes('q-mr-sm')
                                ui.button('Remove Employee',
                                          on_click=lambda: remove_employee(emp_id),
                                          color='negative')
                    else:
                        employee_name_display.text = "Employee not found"
                        employee_type_display.text = ""
                        ui.notify('Employee not found with that ID', color='warning')

            except Exception as e:
                ui.notify(f"Error fetching employee details: {e}", color='negative')

        def remove_employee(emp_id):
            call_query = sql.SQL('CALL {proc}({ph})').format(
                proc=sql.Identifier('sp_remove_employee'),
                ph=sql.SQL("CAST({} AS INTEGER)").format(sql.Placeholder())
            )

            max_retries = 5
            for attempt in range(1, max_retries + 1):
                try:
                    # Set isolation level to REPEATABLE READ
                    conn.isolation_level = 3
                    with conn.transaction():
                        conn.execute(call_query, [emp_id])
                    ui.notify("Employee removed successfully", color='positive')
                    dialog.close()
                    break
                except Exception as e:
                    if "active master" in str(e):
                        ui.notify("Cannot remove employee who is an active master", color='negative')
                        break
                    elif "not found" in str(e):
                        ui.notify("Employee not found", color='negative')
                        break
                    elif attempt == max_retries:
                        ui.notify(f"Failed to remove employee after {max_retries} attempts: {e}", color='negative')
                    else:
                        continue
                finally:
                    conn.isolation_level = None

        # Add lookup button next to employee ID input
        with ui.row().classes('items-end'):
            ui.button('Look up', on_click=fetch_employee_info).classes('q-ml-sm')

    return dialog
