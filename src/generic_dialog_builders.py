from psycopg import sql
from nicegui import ui

from src.ui_common import display_result
from src.utils import create_date_input_field


def get_table_columns(conn, table_name, schema='public'):
    query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position;
    """
    with conn.cursor() as cur:
        cur.execute(query, (schema, table_name))
        return cur.fetchall()


def submit_add(conn, table_name, input_fields):
    columns = []
    values = []
    identifiers = []

    for col_name, input_component in input_fields.items():
        value = input_component.value
        if value is not None and value != '':
            columns.append(col_name)
            values.append(value)
            identifiers.append(sql.Identifier(col_name))

    if not columns:
        ui.notify('No data to insert.')
        return

    query = sql.SQL("INSERT INTO {table} ({fields}) VALUES ({placeholders})").format(
        table=sql.Identifier(table_name),
        fields=sql.SQL(', ').join(identifiers),
        placeholders=sql.SQL(', ').join(sql.Placeholder() for _ in columns)
    )
    try:
        with conn.cursor() as cur:
            with conn.transaction():
                cur.execute(query, values)
        ui.notify('Row inserted successfully.')
    except Exception as e:
        ui.notify(f'Error inserting row: {e}')


def build_generic_add_dialog(conn, table_name):
    columns = get_table_columns(conn, table_name)
    input_fields = {}

    with ui.dialog() as dialog, ui.card():
        ui.label(f'Insert into {table_name}').classes('text-h6')
        for col_name, data_type, is_nullable in columns:
            label = f"{col_name} ({data_type})"
            if data_type in ('integer', 'bigint', 'smallint', 'numeric', 'real', 'double precision', 'decimal'):
                input_fields[col_name] = ui.number(label=label)
            elif data_type in 'boolean':
                input_fields[col_name] = ui.checkbox(text=label)
            elif data_type in 'date':
                input_fields[col_name] = create_date_input_field(label)
            else:
                input_fields[col_name] = ui.input(label=label)
        ui.button('Submit', on_click=lambda: submit_add(conn, table_name, input_fields)).classes('q-btn-primary')
    return dialog


def get_primary_keys(conn, table_name: str, schema: str = 'public') -> list[str]:
    query = """
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY'
          AND tc.table_schema = %s
          AND tc.table_name = %s
        ORDER BY kcu.ordinal_position;
    """
    with conn.cursor() as cur:
        cur.execute(query, (schema, table_name))
        return [row[0] for row in cur.fetchall()]

def submit_delete(conn, table_name, input_fields):
    where_clauses = []
    params = []
    for col, comp in input_fields.items():
        val = comp.value
        if val is None or val == '':
            ui.notify(f'Не указано значение для {col}', color='negative')
            return
        where_clauses.append(sql.SQL("{col} = {ph}").format(
            col=sql.Identifier(col),
            ph=sql.Placeholder()
        ))
        params.append(val)
    query = sql.SQL("DELETE FROM {tbl} WHERE {conds}").format(
        tbl=sql.Identifier(table_name),
        conds=sql.SQL(' AND ').join(where_clauses)
    )
    try:
        with conn.cursor() as cur:
            with conn.transaction():
                cur.execute(query, params)
        ui.notify('Запись удалена', color='positive')
    except Exception as e:
        ui.notify(f'Ошибка удаления: {e}', color='negative')

def build_generic_delete_dialog(conn, table_name: str):
    pks = get_primary_keys(conn, table_name)
    input_fields = {}
    with ui.dialog() as dialog, ui.card().classes('w-1/3'):
        ui.label(f'Удалить из {table_name}').classes('text-h6')
        if not pks:
            ui.label('У таблицы нет первичного ключа').classes('text-negative')
        else:
            for col in pks:
                comp = create_date_input_field(col) if 'date' in col else ui.input(label=col)
                input_fields[col] = comp
            ui.button('Удалить', on_click=lambda: submit_delete(conn, table_name, input_fields)).classes('q-btn-negative')
    return dialog


def submit_get(conn, table_name, input_fields, result_areas):
    """
    Build and execute a SELECT based on non-empty input_fields,
    then render the result into result_table.
    """
    # collect filters
    where_clauses = []
    params = []
    for col, comp in input_fields.items():
        val = comp.value
        # skip empty filters
        if val is None or val == '':
            continue
        where_clauses.append(
            sql.SQL("{col} = {ph}").format(
                col=sql.Identifier(col),
                ph=sql.Placeholder()
            )
        )
        params.append(val)

    # build base query
    if where_clauses:
        query = sql.SQL("SELECT * FROM {tbl} WHERE {conds}").format(
            tbl=sql.Identifier(table_name),
            conds=sql.SQL(" AND ").join(where_clauses)
        )
    else:
        query = sql.SQL("SELECT * FROM {tbl}").format(
            tbl=sql.Identifier(table_name)
        )

    # execute and fetch
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            cols = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
    except Exception as e:
        ui.notify(f"Error fetching rows: {e}", color="negative")
        return

    display_result(table_name, cols, rows, result_areas)

def build_generic_get_dialog(conn, table_name, result_areas):
    """
    Build a dialog that lets the user filter any subset of columns,
    and then plugs results into result_table.
    """
    columns = get_table_columns(conn, table_name)
    input_fields = {}

    with ui.dialog() as dialog, ui.card().classes('w-1/2'):
        ui.label(f'Filter {table_name}').classes('text-h6 q-mb-sm')
        # one input per column
        for col_name, data_type, is_nullable in columns:
            label = f"{col_name} ({data_type})"
            if data_type in ('integer', 'bigint', 'smallint', 'numeric', 'real', 'double precision', 'decimal'):
                input_fields[col_name] = ui.number(label=label)
            elif data_type == 'boolean':
                input_fields[col_name] = ui.checkbox(text=label)
            elif data_type == 'date':
                input_fields[col_name] = create_date_input_field(label)
            else:
                input_fields[col_name] = ui.input(label=label)

        with ui.row().classes('q-pt-sm justify-end'):
            ui.button(
                'Get rows',
                on_click=lambda: (submit_get(conn, table_name, input_fields, result_areas), dialog.close())
            ).classes('q-btn-primary')

    return dialog


def submit_update(conn, table_name, pk_fields, update_fields):
    """
    Execute an UPDATE SQL statement based on primary key fields and update fields.
    """
    # Collect WHERE conditions (primary keys)
    where_clauses = []
    where_params = []

    for col, comp in pk_fields.items():
        val = comp.value
        if val is None or val == '':
            ui.notify(f'Primary key {col} value is required', color='negative')
            return
        where_clauses.append(sql.SQL("{col} = {ph}").format(
            col=sql.Identifier(col),
            ph=sql.Placeholder()
        ))
        where_params.append(val)

    # Collect SET clause (columns to update)
    set_clauses = []
    set_params = []

    for col, comp in update_fields.items():
        val = comp.value
        if val is not None and val != '':
            set_clauses.append(sql.SQL("{col} = {ph}").format(
                col=sql.Identifier(col),
                ph=sql.Placeholder()
            ))
            set_params.append(val)

    if not set_clauses:
        ui.notify('No data to update.', color='negative')
        return

    # Construct UPDATE query
    query = sql.SQL("UPDATE {table} SET {set_clause} WHERE {where_clause}").format(
        table=sql.Identifier(table_name),
        set_clause=sql.SQL(', ').join(set_clauses),
        where_clause=sql.SQL(' AND ').join(where_clauses)
    )

    params = set_params + where_params

    try:
        with conn.cursor() as cur:
            with conn.transaction():
                cur.execute(query, params)
                if cur.rowcount == 0:
                    ui.notify('No rows were updated. Check primary key values.', color='warning')
                else:
                    ui.notify(f'Updated {cur.rowcount} row(s) successfully.', color='positive')
    except Exception as e:
        ui.notify(f'Error updating row: {e}', color='negative')


def build_generic_update_dialog(conn, table_name):
    """
    Build a dialog for updating rows in a table.
    """
    columns = get_table_columns(conn, table_name)
    pks = get_primary_keys(conn, table_name)

    pk_fields = {}
    update_fields = {}

    with ui.dialog() as dialog, ui.card().classes('w-2/3'):
        ui.label(f'Update {table_name}').classes('text-h6')

        # If no primary keys, show a warning
        if not pks:
            ui.label('Table has no primary key. Cannot update without identifying a unique row.').classes(
                'text-negative')
            return dialog

        # Create primary key fields section
        ui.label('Identify row to update:').classes('text-subtitle1 q-mt-md')
        with ui.card().classes('q-mb-md'):
            for col_name in pks:
                # Find the column type from columns list
                col_info = next((col for col in columns if col[0] == col_name), None)
                if col_info:
                    col_name, data_type, is_nullable = col_info
                    label = f"{col_name} ({data_type})"
                    if data_type in ('integer', 'bigint', 'smallint', 'numeric', 'real', 'double precision', 'decimal'):
                        pk_fields[col_name] = ui.number(label=label)
                    elif data_type == 'boolean':
                        pk_fields[col_name] = ui.checkbox(text=label)
                    elif data_type == 'date':
                        pk_fields[col_name] = create_date_input_field(label)
                    else:
                        pk_fields[col_name] = ui.input(label=label)

        # Create update fields section
        ui.label('New values:').classes('text-subtitle1 q-mt-md')
        with ui.card():
            for col_name, data_type, is_nullable in columns:
                # Skip primary key columns in the update section
                if col_name in pks:
                    continue

                label = f"{col_name} ({data_type})"
                if data_type in ('integer', 'bigint', 'smallint', 'numeric', 'real', 'double precision', 'decimal'):
                    update_fields[col_name] = ui.number(label=label)
                elif data_type == 'boolean':
                    update_fields[col_name] = ui.checkbox(text=label)
                elif data_type == 'date':
                    update_fields[col_name] = create_date_input_field(label)
                else:
                    update_fields[col_name] = ui.input(label=label)

        with ui.row().classes('q-pt-md justify-end'):
            ui.button('Update',
                      on_click=lambda: submit_update(conn, table_name, pk_fields, update_fields)
                      ).classes('q-btn-primary')

    return dialog
