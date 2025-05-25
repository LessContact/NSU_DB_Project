from nicegui import ui

def create_date_input_field(label):
    with ui.input(label) as date:
        with ui.menu().props('no-parent-event') as menu:
            with ui.date().bind_value(date):
                with ui.row().classes('justify-end'):
                    ui.button('Close', on_click=menu.close).props('flat')
        with date.add_slot('append'):
            ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
    return date
