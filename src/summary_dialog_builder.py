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
        for filter_name, filter_config_entry in config.items(): # Renamed to avoid shadowing

            # Case 1: Database lookup -> ('table', 'name_col', 'id_col')
            if isinstance(filter_config_entry, tuple) and len(filter_config_entry) == 3:
                table, name_col, id_col = filter_config_entry
                query = sql.SQL("SELECT DISTINCT {id}, {name} FROM {tbl} ORDER BY {name}").format(
                    id=sql.Identifier(id_col),
                    name=sql.Identifier(name_col),
                    tbl=sql.Identifier(table)
                )
                cur.execute(query)
                rows = cur.fetchall()
                options = [row[1] for row in rows]
                id_map = {row[1]: row[0] for row in rows}
                filter_data[filter_name] = {'options': options, 'id_map': id_map}

            # Case 2: Hardcoded list of options
            elif isinstance(filter_config_entry, list):
                id_map = {opt: opt for opt in filter_config_entry}
                filter_data[filter_name] = {'options': filter_config_entry, 'id_map': id_map}

            # Case 3: Boolean type
            elif filter_config_entry == 'boolean':
                filter_data[filter_name] = {
                    'options': ['Yes', 'No'],
                    'id_map': {'Yes': True, 'No': False}
                }

            # Case 4: Date types (MODIFIED)
            elif isinstance(filter_config_entry, str) and filter_config_entry == 'date':
                filter_data[filter_name] = {'type': 'date'}
            elif isinstance(filter_config_entry, str) and filter_config_entry.startswith('date_range_start:'):
                parts = filter_config_entry.split(':', 1)
                if len(parts) == 2 and parts[1]:
                    filter_data[filter_name] = {'type': 'date_range_start', 'target_column': parts[1]}
                else:
                    raise ValueError(f"Invalid date_range_start format for '{filter_name}': {filter_config_entry}")
            elif isinstance(filter_config_entry, str) and filter_config_entry.startswith('date_range_end:'):
                parts = filter_config_entry.split(':', 1)
                if len(parts) == 2 and parts[1]:
                    filter_data[filter_name] = {'type': 'date_range_end', 'target_column': parts[1]}
                else:
                    raise ValueError(f"Invalid date_range_end format for '{filter_name}': {filter_config_entry}")
            else:
                raise TypeError(f"Unsupported filter configuration for '{filter_name}': {filter_config_entry}")
    return filter_data


def common_summary_dialog_builder(conn, table_name, result_areas):
    """
    Generic builder for summary dialogs based on FILTER_CONFIG.
    `table_name` is the key from FILTER_CONFIG (view or function name).
    """
    dialog_name = table_name

    try:
        filter_options_data = get_filter_options(conn, dialog_name)
    except Exception as e:
        ui.notify(f"Error fetching filter options for {dialog_name}: {e}", color='negative')
        return ui.dialog()

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-xl'):
        title_label_text = dialog_name.replace('_', ' ').title()
        ui.label(f'Summary: {title_label_text}').classes('text-h6')

        inputs = {}
        all_config_keys_ordered = list(FILTER_CONFIG[dialog_name].keys())

        for name in all_config_keys_ordered:
            data = filter_options_data[name]
            label_text = name[2:].replace('_', ' ').title() if name.startswith('p_') else name.replace('_', ' ').title()

            # MODIFIED: UI Element Creation for dates
            filter_type_str = data.get('type', '')
            if filter_type_str == 'date' or \
                    filter_type_str == 'date_range_start' or \
                    filter_type_str == 'date_range_end':
                inputs[name] = create_date_input_field(label_text)
            elif 'options' in data:  # Covers boolean, list, DB lookup
                current_options = ["Any"] + data['options']
                inputs[name] = ui.select(current_options, label=label_text, value="Any").classes('w-full')

        def on_submit():
            dialog_is_function = dialog_name.startswith("get_")
            fn_call_args = []
            fn_call_placeholders = []
            where_clauses = []
            where_params = []

            function_param_keys_in_order = [k for k in all_config_keys_ordered if k.startswith('p_')]
            for p_key in function_param_keys_in_order:
                p_config_detail = filter_options_data[p_key]
                p_ui_input = inputs[p_key]
                p_value = p_ui_input.value

                # p_ parameter date types are simple 'date', not range types for direct function args
                if p_config_detail.get('type') == 'date':
                    if not p_value:
                        # Make p_ date parameters optional if "Any" could be chosen,
                        # or keep them mandatory as they are often for functions.
                        # For now, assuming date params for functions are mandatory if configured.
                        ui.notify(f"{p_key[2:].replace('_', ' ').title()} is required.", color='negative')
                        return
                    fn_call_args.append(p_value)
                elif 'options' in p_config_detail:
                    if p_value == "Any":
                        fn_call_args.append(None)
                    else:
                        fn_call_args.append(p_config_detail['id_map'][p_value])
                fn_call_placeholders.append(sql.SQL('%s'))

            for filter_key in all_config_keys_ordered:
                if filter_key.startswith("p_") and dialog_is_function:
                    continue

                config_detail = filter_options_data[filter_key]
                ui_input_element = inputs[filter_key]
                value = ui_input_element.value

                if value is None or (isinstance(value, str) and value == "Any"):
                    continue

                # MODIFIED: WHERE clause construction for date filters
                filter_type = config_detail.get('type')

                if filter_type == 'date':
                    where_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(filter_key)))
                    where_params.append(value)
                elif filter_type == 'date_range_start':
                    target_col_name = config_detail.get('target_column')
                    if not target_col_name:
                        ui.notify(f"Config error for {filter_key}: missing target_column.", color='negative')
                        continue
                    where_clauses.append(sql.SQL("{} >= %s").format(sql.Identifier(target_col_name)))
                    where_params.append(value)
                elif filter_type == 'date_range_end':
                    target_col_name = config_detail.get('target_column')
                    if not target_col_name:
                        ui.notify(f"Config error for {filter_key}: missing target_column.", color='negative')
                        continue
                    where_clauses.append(sql.SQL("{} <= %s").format(sql.Identifier(target_col_name)))
                    where_params.append(value)
                elif 'options' in config_detail:  # List, DB lookup, Boolean
                    actual_value = config_detail['id_map'][value]
                    if isinstance(actual_value, bool):
                        where_clauses.append(
                            sql.SQL("{} = {}").format(sql.Identifier(filter_key), sql.Literal(actual_value)))
                    else:
                        where_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(filter_key)))
                        where_params.append(actual_value)

            final_query = None
            final_params = []

            if dialog_is_function:
                base_fn_sql = sql.SQL("SELECT * FROM {function_name}({params})").format(
                    function_name=sql.Identifier(dialog_name),
                    params=sql.SQL(', ').join(fn_call_placeholders) if fn_call_placeholders else sql.SQL("")
                )
                final_params.extend(fn_call_args)
                if where_clauses:
                    final_query = sql.SQL("SELECT * FROM ({base_query}) AS func_result WHERE {conditions}").format(
                        base_query=base_fn_sql,
                        conditions=sql.SQL(" AND ").join(where_clauses)
                    )
                    final_params.extend(where_params)
                else:
                    final_query = base_fn_sql
            else:  # It's a view
                base_view_sql = sql.SQL("SELECT * FROM {view_name}").format(view_name=sql.Identifier(dialog_name))
                final_params.extend(where_params)
                if where_clauses:
                    final_query = sql.SQL("{base} WHERE {conditions}").format(
                        base=base_view_sql,
                        conditions=sql.SQL(" AND ").join(where_clauses)
                    )
                else:
                    final_query = base_view_sql

            try:
                with conn.cursor() as cur:
                    # print(f"Executing generic query: {final_query.as_string(conn) if conn else str(final_query)}")
                    # print(f"With generic params: {final_params}")
                    cur.execute(final_query, final_params)
                    cols = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()
                if rows:
                    display_result(dialog_name, cols, rows, result_areas)
                else:
                    ui.notify("No results found.", color='info')
                dialog.close()
            except OperationalError as oe:
                ui.notify(f"Database error: {oe}", color='negative')
            except Exception as e:
                ui.notify(f"An unexpected error occurred: {e}", color='negative')

        ui.button('Fetch Summary', on_click=on_submit).classes('q-mt-md')
        ui.button('Cancel', on_click=dialog.close).props('outline')
    return dialog


# Register the common_summary_dialog_builder for all entries in FILTER_CONFIG.
# This will use the common builder for any key defined in FILTER_CONFIG.
# If a specific dialog builder for a key was registered before this loop,
# it would be overwritten by this registration.
for config_key in FILTER_CONFIG:
    register_dialog(config_key)(common_summary_dialog_builder)
