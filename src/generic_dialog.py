from psycopg import sql
from nicegui import ui
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


def submit_form(conn, table_name, input_fields):
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
            cur.execute(query, values)
        conn.commit()
        ui.notify('Row inserted successfully.')
    except Exception as e:
        conn.rollback()
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
        ui.button('Submit', on_click=lambda: submit_form(conn, table_name, input_fields)).classes('q-btn-primary')
    return dialog
