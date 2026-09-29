from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel,
                             QPushButton, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import pyqtSignal, QTimer, QDateTime, Qt
from PyQt6.QtGui import QPixmap
from views.ventas_view import VentasWidget
from views.almaceno_view import AlmacenWidget
from views.economia_view import EconomiaWidget
from views.admin_view import AdminWidget
from config import APP_NAME, APP_VERSION, APP_AUTHOR, APP_GITHUB_URL, LOGO_PATH
import os


class MainWindow(QMainWindow):
    logout_signal = pyqtSignal()
    exit_signal = pyqtSignal()

    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.setWindowTitle(f"{APP_NAME} - Sesión: {user_data['full_name']} ({user_data['role'].upper()})")
        self.setMinimumSize(1100, 700)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        top_bar = QHBoxLayout()
        logo = QLabel()
        logo.setFixedSize(40, 40)
        if os.path.exists(LOGO_PATH):
            pix = QPixmap(LOGO_PATH)
            logo.setPixmap(pix.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        top_bar.addWidget(logo)

        lbl_user_info = QLabel(f"<b>Usuario:</b> {user_data['full_name']} | <b>Rol:</b> <font color='#00f0ff'>{user_data['role'].upper()}</font>")
        top_bar.addWidget(lbl_user_info)
        top_bar.addStretch()

        self.lbl_datetime = QLabel()
        self.lbl_datetime.setStyleSheet("color: #00f0ff; font-weight: bold;")
        top_bar.addWidget(self.lbl_datetime)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)
        self.update_datetime()

        btn_about = QPushButton("Acerca de")
        btn_about.clicked.connect(self.show_about)
        top_bar.addWidget(btn_about)

        btn_logout = QPushButton("Cerrar Sesión")
        btn_logout.setObjectName("btn_danger")
        btn_logout.clicked.connect(self.logout)
        top_bar.addWidget(btn_logout)

        btn_exit = QPushButton("Salir")
        btn_exit.setObjectName("btn_danger")
        btn_exit.clicked.connect(self.exit_application)
        top_bar.addWidget(btn_exit)
        main_layout.addLayout(top_bar)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        self.setup_roles_and_tabs()

    def update_datetime(self):
        self.lbl_datetime.setText(QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm:ss"))

    def logout(self):
        self.logout_signal.emit()

    def exit_application(self):
        self.exit_signal.emit()

    def show_about(self):
        QMessageBox.about(self, f"Acerca de {APP_NAME}",
                          f"<h2>{APP_NAME}</h2>"
                          f"<p><b>Versión:</b> {APP_VERSION}</p>"
                          f"<p><b>Creador:</b> {APP_AUTHOR}</p>"
                          f"<p><b>Interfaz:</b> PyQt6</p>"
                          f"<p><b>Base de datos:</b> SQLite</p>"
                          f"<p><b>Lenguaje:</b> Python 3</p>"
                          f"<p><b>Código fuente:</b><br>{APP_GITHUB_URL}</p>")

    def setup_roles_and_tabs(self):
        role = self.user_data['role']
        self.ventas_widget = VentasWidget(self.user_data)
        self.almacen_widget = AlmacenWidget()
        self.economia_widget = EconomiaWidget()
        self.admin_widget = AdminWidget()

        self.almacen_widget.product_updated_signal.connect(self.ventas_widget.load_catalog_cards)
        self.almacen_widget.product_updated_signal.connect(self.economia_widget.refresh_all)
        self.economia_widget.product_updated_signal.connect(self.ventas_widget.load_catalog_cards)
        self.economia_widget.product_updated_signal.connect(self.almacen_widget.load_products_cards)
        self.ventas_widget.product_sold_signal.connect(self.almacen_widget.load_products_cards)
        self.ventas_widget.product_sold_signal.connect(self.economia_widget.refresh_all)

        if role == 'admin':
            self.tabs.addTab(self.ventas_widget, "🛒 Ventas / Carrito")
            self.tabs.addTab(self.almacen_widget, "📦 Almacén e Inventario")
            self.tabs.addTab(self.economia_widget, "💰 Economía y Entradas")
            self.tabs.addTab(self.admin_widget, "⚙️ Administración")
        elif role == 'vendedor':
            self.tabs.addTab(self.ventas_widget, "🛒 Ventas / Carrito")
        elif role == 'almacenero':
            self.tabs.addTab(self.almacen_widget, "📦 Almacén e Inventario")
        elif role == 'economia':
            self.tabs.addTab(self.economia_widget, "💰 Economía y Entradas")
