from nicegui import ui
from db import db_manager

class User:
    role: str

    def __init__(self, role: str = ''):
        self.role = role

    def get_role(self) -> str:
        return self.role

    def change_role(self, new_role: str) -> bool:
        success = db_manager.connect(new_role)
        if success:
            self.role = new_role
        return success

    def logout(self):
        self.role = ''
        ui.notify(f"Logged out")
        db_manager.disconnect()
