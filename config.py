import os

APP_NAME = "NEXA POS"
APP_VERSION = "3.0.0"
APP_AUTHOR = "Z3r0X"
APP_GITHUB_URL = "https://github.com/Z3r0X-cu/NEXA-POS"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nexa.db")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
PDF_DIR = os.path.join(BASE_DIR, "pdf_reports")
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

CYBERPUNK_QSS = """
QMainWindow, QDialog { background-color: #08090d; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
QWidget { background-color: #08090d; color: #e0e0e0; }
QFrame.MiniCard { background-color: #11131c; border: 1px solid #1f2333; border-radius: 6px; padding: 4px; }
QFrame.MiniCardAlert { background-color: #2a0813; border: 1px solid #ff0055; border-radius: 6px; padding: 4px; }
QPushButton { background-color: #121625; border: 1px solid #00f0ff; color: #00f0ff; border-radius: 4px; padding: 5px 10px; font-weight: bold; }
QPushButton:hover { background-color: #00f0ff; color: #08090d; }
QPushButton#btn_danger { border: 1px solid #ff0055; color: #ff0055; }
QPushButton#btn_danger:hover { background-color: #ff0055; color: #ffffff; }
QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QDateEdit { background-color: #121520; border: 1px solid #282e42; color: #ffffff; border-radius: 4px; padding: 4px; }
QHeaderView::section { background-color: #121520; color: #00f0ff; border: 1px solid #282e42; font-weight: bold; }
QTableWidget { background-color: #0d0f17; gridline-color: #1a1f30; }
"""
