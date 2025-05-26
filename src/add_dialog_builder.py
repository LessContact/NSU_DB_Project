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


def fetch_options(conn):
    """
    Fetches option lists and ID mappings for select widgets in one cursor context.
    Returns a tuple (options, id_maps) where:
      - options is a dict of lists for UI selects
      - id_maps is a dict of dicts mapping name -> id
    """
    tables = {
        "grade":    ("grades",      "grade_title", "g_id"),
        "worker_type": ("worker_types","name",        "tp_id"),
        "brigade":  ("brigade",     "name",        "b_id"),
        "specialisation": ("work_types",  "name",        "t_id"),
        "section":  ("sections",    "name",        "s_id"),
        "lab":      ("labs",        "name",        "l_id"),
    }

    options = {}
    id_maps = {}
    with conn.cursor() as cur:
        for key, (tbl, namecol, idcol) in tables.items():
            q = sql.SQL("SELECT {id}, {name} FROM {tbl} ORDER BY {id}").format(
                id  = sql.Identifier(idcol),
                name= sql.Identifier(namecol),
                tbl = sql.Identifier(tbl)
            )
            cur.execute(q)
            rows = cur.fetchall()
            # build option list and id map
            options[f"{key}_options"] = [row[1] for row in rows]
            id_maps[f"{key}_map"]      = {row[1]: row[0] for row in rows}

    return options, id_maps

@register_dialog('employees')
def build_employees_dialog(conn, table_name):
    try:
        opts, id_maps = fetch_options(conn)
    except Exception as e:
        ui.notify(f"Error fetching options: {e}", color='negative')
        opts = {k + '_options': [] for k in ['grade', 'worker_type', 'brigade', 'specialisation', 'section', 'lab']}
        id_maps = {k + '_map': {} for k in ['grade', 'worker_type', 'brigade', 'specialisation', 'section', 'lab']}

    with ui.dialog() as dialog, ui.card().classes('w-1/2'):
        ui.label('Add Employee').classes('text-h6')
        name = ui.input(label='Full Name')
        hire_date = create_date_input_field("Hire Date")
        worker_type = ui.select(opts['worker_type_options'], label='Employee Type')
        experience = ui.number(label='Experience (years)')
        grade = ui.select(opts['grade_options'], label='Grade')

        brigade_input = ui.select(opts['brigade_options'], label='Brigade')
        spec_input = ui.select(opts['specialisation_options'], label='Specialisation')

        is_brig = ui.checkbox(text='Is Brigadier')
        education = ui.input(label='Education', placeholder='e.g. Bachelor\'s Degree')
        wsh_super = ui.checkbox(text='Is Workshop Supervisor')
        master = ui.checkbox(text='Is Master')
        section_input = ui.select(opts['section_options'], label='Section')
        lab_input = ui.select(opts['lab_options'], label='Lab')

        def on_submit():

            full_name = name.value
            hire_val = hire_date.value
            wt_name = worker_type.value
            exp_val = experience.value
            grade_name = grade.value
            brigade_name = brigade_input.value or None
            spec_name = spec_input.value or None
            is_brig_val = is_brig.value or False
            educ_val = education.value or None
            wsh_val = wsh_super.value or False
            master_val = master.value or False
            section_name = section_input.value or None
            lab_name = lab_input.value or None

            try:
                wt_id = id_maps['worker_type_map'][wt_name]
                grade_id = id_maps['grade_map'][grade_name]
                brig_id = id_maps['brigade_map'].get(brigade_name)
                spec_id = id_maps['specialisation_map'].get(spec_name)
                sect_id = id_maps['section_map'].get(section_name)
                lab_id = id_maps['lab_map'].get(lab_name)
            except KeyError as e:
                ui.notify(f"Invalid selection: {e}", color='negative')
                return

            sql_types = [
                'VARCHAR',    # p_full_name
                'INTEGER',    # p_worker_type
                'INTEGER',    # p_experience
                'INTEGER',    # p_grade_id
                'DATE',       # p_hire_date
                'INTEGER',    # p_brigade_id
                'INTEGER',    # p_specialisation
                'BOOLEAN',    # p_is_brigadier
                'VARCHAR',    # p_education
                'BOOLEAN',    # p_is_wsh_super
                'BOOLEAN',    # p_is_master
                'INTEGER',    # p_section
                'INTEGER',    # p_lab_id
            ]
            # Generate placeholders with casts: $1::VARCHAR, $2::INTEGER, ...
            cast_phs = [
                sql.SQL("CAST({} AS {})").format(sql.Placeholder(), sql.SQL(pg_type))
                for pg_type in sql_types
            ]
            call_q = sql.SQL('CALL {proc}({phs})').format(
                proc = sql.Identifier('sp_add_employee'),
                phs  = sql.SQL(', ').join(cast_phs)
            )
            params = [
                full_name,
                wt_id,
                exp_val,
                grade_id,
                hire_val,
                brig_id,
                spec_id,
                is_brig_val,
                educ_val,
                wsh_val,
                master_val,
                sect_id,
                lab_id
            ]
            try:
                with conn.cursor() as cur:
                    cur.execute("BEGIN ISOLATION LEVEL REPEATABLE READ")
                    cur.execute(call_q, params)
                conn.commit()
                ui.notify("Employee created via stored procedure")
                dialog.close()
            except Exception as e:
                conn.rollback()
                ui.notify(f"Error calling sp_add_employee: {e}", color='negative')

        ui.button('Create', on_click=on_submit).classes('q-btn-primary')
    return dialog

# TEMP------------------------------------------
@register_dialog('workers')
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

