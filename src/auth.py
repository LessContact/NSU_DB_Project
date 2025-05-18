from nicegui import ui


class User:
    role: str

    def __init__(self, role: str = ''):
        self.role = role

    def get_role(self) -> str:
        return self.role

    def change_role(self, new_role: str):
        self.role = new_role
        ui.notify(f"Role changed to {new_role}")
        # db_manager.connect(new_role)

    def logout(self):
        self.role = ''
        ui.notify(f"Logged out")
        # db_manager.disconnect()
