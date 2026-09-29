import sys
from PyQt6.QtWidgets import QApplication
from database import init_db, get_connection
from views.login_view import LoginWidget
from views.main_window import MainWindow
from config import APP_VERSION


def create_default_admin():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO users (username, password, full_name, ci, address, phone, role)
            VALUES ('admin', 'admin1234', 'Administrador Principal', '00000000000', 'Sede Central', '00000000', 'admin')
        """)
        conn.commit()
    conn.close()


class AppManager:
    def __init__(self):
        self.login_window = LoginWidget()
        self.main_window = None
        self.login_window.login_success_signal.connect(self.open_main_window)
        self.login_window.exit_requested_signal.connect(self.exit_app)
        self.login_window.show()

    def open_main_window(self, user_data):
        self.main_window = MainWindow(user_data)
        self.main_window.logout_signal.connect(self.show_login)
        self.main_window.exit_signal.connect(self.exit_app)
        self.main_window.show()
        self.login_window.hide()

    def show_login(self):
        if self.main_window:
            self.main_window.close()
            self.main_window.deleteLater()
            self.main_window = None
        self.login_window.txt_password.clear()
        self.login_window.txt_username.setFocus()
        self.login_window.show()

    def exit_app(self):
        QApplication.instance().quit()


if __name__ == "__main__":
    init_db()
    create_default_admin()

    app = QApplication(sys.argv)
    app.setApplicationName("NEXA POS")
    app.setApplicationVersion(APP_VERSION)
    app.setStyleSheet("""
        QWidget { background-color: #121216; color: #e0e0e0; font-family: 'Segoe UI', Arial, sans-serif; }
        QLineEdit, QComboBox, QDoubleSpinBox, QDateEdit, QListWidget, QTableWidget {
            background-color: #1a1a24; border: 1px solid #33334d; border-radius: 4px;
            padding: 5px; color: #ffffff;
        }
        QPushButton { background-color: #00f0ff; color: #000000; border: none; border-radius: 4px;
            padding: 8px 12px; font-weight: bold; }
        QPushButton:hover { background-color: #70f8ff; }
        QPushButton#btn_danger { background-color: #ff0055; color: #ffffff; }
        QPushButton#btn_danger:hover { background-color: #ff407d; }
        QHeaderView::section { background-color: #1a1a24; color: #00f0ff; padding: 4px; border: 1px solid #33334d; }
        QFrame[class="MiniCard"] { background-color: #181824; border: 1px solid #2a2a3d; border-radius: 6px; }
        QFrame[class="MiniCardAlert"] { background-color: #2a121d; border: 1px solid #ff0055; border-radius: 6px; }
    """)

    manager = AppManager()
    sys.exit(app.exec())
