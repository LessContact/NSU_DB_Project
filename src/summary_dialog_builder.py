from typing import Callable
from nicegui import ui
from psycopg import sql, OperationalError, IsolationLevel

from ui_common import display_result
from utils import create_date_input_field
from view_filter_config import FILTER_CONFIG

summary_dialog_builders: dict[str, Callable] = {}

def register_dialog(table_name: str):
    def decorator(fn: Callable):
        summary_dialog_builders[table_name] = fn
        return fn
    return decorator


def get_filter_options(conn, name) -> dict:
    """
    Generates a dictionary of available filter options for a given view or function.

    This function reads from a predefined FILTER_CONFIG to determine which filters
    are available for the given `name` and how to fetch their possible values
    (e.g., from a database table, a hardcoded list, or special types like boolean/date).

    Args:
        conn: An active psycopg3 database connection.
        name: The name of the database view or function (e.g., 'v_staff_composition').

    Returns:
        A dictionary where each key is a filter's name and the value is another
        dictionary containing its details.
        - For DB lookups: {'options': ['Name1', 'Name2'], 'id_map': {'Name1': 1, 'Name2': 2}}
        - For lists: {'options': ['Val1', 'Val2'], 'id_map': {'Val1': 'Val1', ...}}
        - For booleans: {'options': ['Yes', 'No'], 'id_map': {'Yes': True, 'No': False}}
        - For dates: {'type': 'date'}

    Raises:
        ValueError: If the provided `name` is not found in FILTER_CONFIG.
        TypeError: If an unknown filter configuration type is encountered.
    """
    if name not in FILTER_CONFIG:
        raise ValueError(f"No filter configuration found for '{name}'")

    config = FILTER_CONFIG[name]
    filter_data = {}

    with conn.cursor() as cur:
        for filter_name, filter_config in config.items():

            # Case 1: Database lookup -> ('table', 'name_col', 'id_col')
            if isinstance(filter_config, tuple) and len(filter_config) == 3:
                table, name_col, id_col = filter_config

                query = sql.SQL("SELECT DISTINCT {id}, {name} FROM {tbl} ORDER BY {name}").format(
                    id=sql.Identifier(id_col),
                    name=sql.Identifier(name_col),
                    tbl=sql.Identifier(table)
                )

                cur.execute(query)
                rows = cur.fetchall()

                # For UI dropdowns (e.g. ['Workshop A', 'Workshop B'])
                options = [row[1] for row in rows]
                # For mapping the selected name back to its ID
                id_map = {row[1]: row[0] for row in rows}

                filter_data[filter_name] = {'options': options, 'id_map': id_map}

            # Case 2: Hardcoded list of options
            elif isinstance(filter_config, list):
                # The value is its own "ID"
                id_map = {opt: opt for opt in filter_config}
                filter_data[filter_name] = {'options': filter_config, 'id_map': id_map}

            # Case 3: Boolean type
            elif filter_config == 'boolean':
                filter_data[filter_name] = {
                    'options': ['Yes', 'No'],
                    'id_map': {'Yes': True, 'No': False}
                }

            # Case 4: Date type
            elif filter_config == 'date':
                # This is a special marker for the UI to render a date picker
                filter_data[filter_name] = {'type': 'date'}

            else:
                raise TypeError(f"Unsupported filter configuration for '{filter_name}': {filter_config}")

    return filter_data


@register_dialog('get_product_assembly_summary')
def get_product_assembly_summary(conn, table_name, result_areas):
    dialog_name = 'get_product_assembly_summary'
    try:
        # Fetch all possible options for dropdowns
        filter_options_data = get_filter_options(conn, dialog_name)
    except Exception as e:
        ui.notify(f"Error fetching options for {dialog_name}: {e}", color='negative')
        return ui.dialog()

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-xl'):
        ui.label(f'Get Product Assembly Summary').classes('text-h6')

        inputs = {}  # To store UI input elements

        # Create UI elements based on filter_options_data
        # Mandatory date parameters for the function
        inputs['p_start_date'] = create_date_input_field("Start Date")
        inputs['p_end_date'] = create_date_input_field("End Date")

        # Optional filters (applied via WHERE clause on the function's result)
        for name, data in filter_options_data.items():
            if name in ['p_start_date', 'p_end_date']:  # Already created
                continue

            current_options = ["Any"] + data['options']
            inputs[name] = ui.select(current_options, label=name.replace('_', ' ').title(), value="Any").classes(
                'w-full')
            # No boolean or other specific types for this function's optional filters based on config

        def on_submit():

            start_date_str = inputs['p_start_date'].value
            end_date_str = inputs['p_end_date'].value

            if not start_date_str or not end_date_str:
                ui.notify("Start Date and End Date are required.", color='negative')
                return

            # Base query calling the function
            # The function itself returns a table, so we select from it
            base_query_sql = sql.SQL("SELECT * FROM {function_name}(%s, %s)").format(
                function_name=sql.Identifier(dialog_name)
            )

            # Parameters for the function call
            fn_params = [start_date_str, end_date_str]

            # Build WHERE clause for optional filters
            where_clauses = []
            where_params = []

            optional_filters = ['agg_level', 'workshop', 'section', 'category']
            for filt_name in optional_filters:
                if filt_name in inputs:
                    value = inputs[filt_name].value
                    if value is not None and value != "Any":
                        # The PL/pgSQL function's WHERE comments indicate filtering by name directly
                        # For agg_level, workshop, section, category, the column names in the
                        # function's output match the filter names.
                        where_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(filt_name)))
                        where_params.append(value)

            final_query = base_query_sql
            final_params = fn_params

            if where_clauses:
                final_query = sql.SQL("SELECT * FROM ({base_query}) AS func_result WHERE {conditions}").format(
                    base_query=base_query_sql,
                    conditions=sql.SQL(" AND ").join(where_clauses)
                )
                final_params.extend(where_params)  # Add where_params after function params

            try:
                with conn.cursor() as cur:
                    print(f"Executing query: {final_query.as_string(conn)}")
                    print(f"With params: {final_params}")
                    cur.execute(final_query, final_params)
                    cols = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()

                if rows:
                    display_result(table_name, cols, rows, result_areas)
                else:
                    ui.notify("No results found.", color='info')

                dialog.close()

            except Exception as e:
                ui.notify(f"An unexpected error occurred: {e}", color='negative')

        ui.button('Fetch Summary', on_click=on_submit).classes('q-mt-md')
        ui.button('Cancel', on_click=dialog.close).props('outline')

    return dialog
