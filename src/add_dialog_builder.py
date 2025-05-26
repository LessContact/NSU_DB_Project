from typing import Callable
from nicegui import ui
from psycopg import sql, OperationalError, IsolationLevel

from src.utils import create_date_input_field

add_dialog_builders: dict[str, Callable] = {}

def register_dialog(table_name: str):
    def decorator(fn: Callable):
        add_dialog_builders[table_name] = fn
        return fn
    return decorator


def fetch_options(conn, table_type='employees'):
    """
    Fetches option lists and ID mappings for select widgets in one cursor context.
    Returns a tuple (options, id_maps) where:
      - options is a dict of lists for UI selects
      - id_maps is a dict of dicts mapping name -> id

    Args:
        conn: Database connection
        table_type: Type of options to fetch ('employees' or 'products')
    """
    if table_type == 'employees':
        tables = {
            "grade": ("grades", "grade_title", "g_id"),
            "worker_type": ("worker_types", "name", "tp_id"),
            "brigade": ("brigade", "name", "b_id"),
            "specialisation": ("work_types", "name", "t_id"),
            "section": ("sections", "name", "s_id"),
            "lab": ("labs", "name", "l_id"),
        }
    elif table_type == 'products':
        tables = {
            "category": ("product_categories", "name", "c_id"),
            "workshop": ("workshops", "name", "wsh_id"),
        }
    else:
        raise ValueError(f"Unsupported table_type: {table_type}")

    options = {}
    id_maps = {}
    with conn.cursor() as cur:
        with conn.transaction():
            for key, (tbl, namecol, idcol) in tables.items():
                q = sql.SQL("SELECT {id}, {name} FROM {tbl} ORDER BY {id}").format(
                    id=sql.Identifier(idcol),
                    name=sql.Identifier(namecol),
                    tbl=sql.Identifier(tbl)
                )
                cur.execute(q)
                rows = cur.fetchall()
                # build option list and id map
                options[f"{key}_options"] = [row[1] for row in rows]
                id_maps[f"{key}_map"] = {row[1]: row[0] for row in rows}

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
            max_retries = 5
            for attempt in range(1, max_retries + 1):
                try:
                    conn.isolation_level = 3 # REPEATABLE READ
                    with conn.transaction():
                        conn.execute(call_q, params)
                    ui.notify("Employee created via stored procedure")
                    dialog.close()
                    break
                except OperationalError as e:
                    if attempt == max_retries:
                        ui.notify(f"Ошибка сериализации после {max_retries} попыток: {e}", color='negative')
                except Exception as e:
                    ui.notify(f"Error calling sp_add_employee: {e}", color='negative')
                    break
                finally:
                    conn.isolation_level = None

        ui.button('Create', on_click=on_submit).classes('q-btn-primary')
    return dialog


@register_dialog('products')
def build_products_dialog(conn, table_name):
    try:
        opts, id_maps = fetch_options(conn, table_type='products')
    except Exception as e:
        ui.notify(f"Error fetching options: {e}", color='negative')
        opts = {k + '_options': [] for k in ['category', 'workshop']}
        id_maps = {k + '_map': {} for k in ['category', 'workshop']}

    with ui.dialog() as dialog, ui.card().classes('w-1/2'):
        ui.label('Add Product').classes('text-h6')

        # Basic product information
        name_input = ui.input(label='Product Name')
        category_input = ui.select(opts['category_options'], label='Category')
        workshop_input = ui.select(opts['workshop_options'], label='Workshop')
        begin_date = create_date_input_field("Begin Date")

        product_type = category_input
        use_type = ui.input(label='Use Type', placeholder='e.g. Combat, Transport')
        vehicle_type = ui.input(label='Vehicle Type', placeholder='e.g. Fixed-wing, Rotary-wing')
        cargo_cap = ui.number(label='Cargo Capacity')
        pass_count = ui.number(label='Passenger Count')
        eng_count = ui.number(label='Engine Count')
        armaments = ui.input(label='Armaments')

        missile_type = ui.input(label='Missile Type')
        payload = ui.number(label='Payload (kg)')
        range_km = ui.number(label='Range (km)')

        text_spec = ui.textarea(label='Text Specification')

        def on_submit():
            # gather core
            p_name = name_input.value
            p_category_name = category_input.value
            p_workshop_name = workshop_input.value
            p_begin = begin_date.value or None
            p_type = product_type.value

            # map to IDs
            try:
                p_category = id_maps['category_map'][p_category_name]
                p_workshop = id_maps['workshop_map'][p_workshop_name]
            except KeyError as e:
                ui.notify(f"Invalid selection: {e}", color='negative')
                return

            p_use_type = use_type.value or None
            p_vehicle_type = vehicle_type.value or None
            p_cargo_cap = cargo_cap.value or None
            p_pass_count = pass_count.value or None
            p_eng_count = eng_count.value or None
            p_armaments = armaments.value or None

            p_missile_type = missile_type.value or None
            p_payload = payload.value or None
            p_range = range_km.value or None

            p_text_spec = text_spec.value or None

            # prepare SQL call
            sql_types = [
                'VARCHAR', 'INTEGER', 'INTEGER', 'DATE',
                'VARCHAR', 'VARCHAR', 'VARCHAR', 'INTEGER',
                'INTEGER', 'INTEGER', 'VARCHAR',
                'VARCHAR', 'INTEGER', 'INTEGER',
                'TEXT'
            ]
            casted = [
                sql.SQL("CAST({} AS {})").format(sql.Placeholder(), sql.SQL(t))
                for t in sql_types
            ]
            call_q = sql.SQL('CALL {proc}({phs})').format(
                proc = sql.Identifier('sp_add_product'),
                phs  = sql.SQL(', ').join(casted)
            )
            params = [
                p_name,
                p_category,
                p_workshop,
                p_begin,
                p_type,
                p_use_type,
                p_vehicle_type,
                p_cargo_cap,
                p_pass_count,
                p_eng_count,
                p_armaments,
                p_missile_type,
                p_payload,
                p_range,
                p_text_spec
            ]

            max_retries = 5
            for attempt in range(1, max_retries+1):
                try:
                    conn.isolation_level = 3  # REPEATABLE READ
                    with conn.transaction():
                        conn.execute(call_q, params)
                    ui.notify(f"Product '{p_name}' created successfully")
                    dialog.close()
                    break
                except OperationalError as e:
                    if attempt == max_retries:
                        ui.notify(f"Serialization failure after {max_retries} attempts: {e}", color='negative')
                except Exception as e:
                    ui.notify(f"Error calling sp_add_product: {e}", color='negative')
                    break
                finally:
                    conn.isolation_level = None

        ui.button('Create', on_click=on_submit).classes('q-btn-primary')

    return dialog
