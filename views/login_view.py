from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from database import get_connection
from config import APP_NAME, APP_VERSION, LOGO_PATH
import os


class LoginWidget(QWidget):
    login_success_signal = pyqtSignal(dict)
    exit_requested_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setFixedSize(380, 370)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

        logo = QLabel()
        logo.setFixedSize(110, 110)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if os.path.exists(LOGO_PATH):
            pix = QPixmap(LOGO_PATH)
            logo.setPixmap(pix.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel(APP_NAME)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #00f0ff; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Usuario")
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setPlaceholderText("Contraseña")
        self.txt_username.returnPressed.connect(self._focus_password)
        self.txt_password.returnPressed.connect(self.authenticate)

        form.addRow("Usuario:", self.txt_username)
        form.addRow("Contraseña:", self.txt_password)
        layout.addLayout(form)

        btn_login = QPushButton("INICIAR SESIÓN")
        btn_login.setStyleSheet("margin-top: 15px; padding: 10px; font-weight: bold;")
        btn_login.clicked.connect(self.authenticate)
        layout.addWidget(btn_login)

    def _focus_password(self):
        self.txt_password.setFocus()

    def authenticate(self):
        username = self.txt_username.text().strip()
        password = self.txt_password.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Atención", "Por favor ingrese usuario y contraseña.")
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, full_name, role FROM users
            WHERE LOWER(username) = LOWER(?) AND password = ?
        """, (username, password))
        user_row = cursor.fetchone()
        conn.close()

        if user_row:
            self.login_success_signal.emit({'id': user_row[0], 'username': user_row[1],
                                            'full_name': user_row[2], 'role': user_row[3]})
        else:
            QMessageBox.critical(self, "Error de Acceso", "Credenciales inválidas. Verifique usuario y contraseña.")
