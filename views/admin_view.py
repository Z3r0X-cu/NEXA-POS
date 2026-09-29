from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, 
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, 
                             QHBoxLayout, QLabel, QFileDialog, QDialog)
from database import get_connection
from utils.image_utils import process_and_crop_square
import uuid
import os
from config import UPLOADS_DIR


class EditUserDialog(QDialog):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Editar Usuario - {user_data['username']}")
        self.setMinimumWidth(380)
        self.user_id = user_data['id']

        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()
        
        self.txt_full_name = QLineEdit(user_data['full_name'])
        self.txt_ci = QLineEdit(user_data['ci'])
        self.txt_address = QLineEdit(user_data['address'])
        self.txt_phone = QLineEdit(user_data['phone'])

        self.cb_role = QComboBox()
        self.cb_role.addItems(['admin', 'almacenero', 'economia', 'vendedor'])
        self.cb_role.setCurrentText(user_data['role'])

        self.txt_new_pass = QLineEdit()
        self.txt_new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_new_pass.setPlaceholderText("Dejar en blanco para no cambiar")

        self.txt_confirm_pass = QLineEdit()
        self.txt_confirm_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_confirm_pass.setPlaceholderText("Repetir nueva contraseña")

        form.addRow("Nombre Completo:", self.txt_full_name)
        form.addRow("CI:", self.txt_ci)
        form.addRow("Dirección:", self.txt_address)
        form.addRow("Teléfono:", self.txt_phone)
        form.addRow("Rol / Permisos:", self.cb_role)
        form.addRow("Nueva Contraseña:", self.txt_new_pass)
        form.addRow("Confirmar Pass:", self.txt_confirm_pass)

        layout.addLayout(form)

        btn_save = QPushButton("GUARDAR CAMBIOS")
        btn_save.clicked.connect(self.save)
        layout.addWidget(btn_save)

    def save(self):
        new_pass = self.txt_new_pass.text().strip()
        confirm_pass = self.txt_confirm_pass.text().strip()

        if new_pass and new_pass != confirm_pass:
            QMessageBox.warning(self, "Error", "Las nuevas contraseñas no coinciden.")
            return

        conn = get_connection()
        cursor = conn.cursor()

        if new_pass:
            cursor.execute("""
                UPDATE users 
                SET full_name = ?, ci = ?, address = ?, phone = ?, role = ?, password = ?
                WHERE id = ?
            """, (self.txt_full_name.text().strip(), self.txt_ci.text().strip(),
                  self.txt_address.text().strip(), self.txt_phone.text().strip(),
                  self.cb_role.currentText(), new_pass, self.user_id))
        else:
            cursor.execute("""
                UPDATE users 
                SET full_name = ?, ci = ?, address = ?, phone = ?, role = ?
                WHERE id = ?
            """, (self.txt_full_name.text().strip(), self.txt_ci.text().strip(),
                  self.txt_address.text().strip(), self.txt_phone.text().strip(),
                  self.cb_role.currentText(), self.user_id))

        conn.commit()
        conn.close()

        QMessageBox.information(self, "Éxito", "Usuario actualizado correctamente.")
        self.accept()


class AdminWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        self.setLayout(layout)

        form_layout = QVBoxLayout()
        form = QFormLayout()

        self.txt_store_name = QLineEdit()
        self.txt_store_address = QLineEdit()
        self.txt_store_phone = QLineEdit()

        form.addRow("--- INFORMACIÓN NEGOCIO ---", QLabel(""))
        form.addRow("Nombre Comercial:", self.txt_store_name)
        form.addRow("Dirección:", self.txt_store_address)
        form.addRow("Teléfono:", self.txt_store_phone)

        btn_save_store = QPushButton("GUARDAR DATOS NEGOCIO")
        btn_save_store.clicked.connect(self.save_store_info)

        self.txt_user = QLineEdit()
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass_confirm = QLineEdit()
        self.txt_pass_confirm.setEchoMode(QLineEdit.EchoMode.Password)

        self.txt_name = QLineEdit()
        self.txt_ci = QLineEdit()
        self.txt_address = QLineEdit()
        self.txt_phone = QLineEdit()
        self.cb_role = QComboBox()
        self.cb_role.addItems(['admin', 'almacenero', 'economia', 'vendedor'])

        self.btn_photo = QPushButton("Subir Foto Perfil")
        self.btn_photo.clicked.connect(self.select_photo)
        self.photo_path = ""

        form.addRow("--- CREAR USUARIO ---", QLabel(""))
        form.addRow("Usuario:", self.txt_user)
        form.addRow("Contraseña:", self.txt_pass)
        form.addRow("Confirmar Contraseña:", self.txt_pass_confirm)
        form.addRow("Nombre Completo:", self.txt_name)
        form.addRow("CI:", self.txt_ci)
        form.addRow("Dirección:", self.txt_address)
        form.addRow("Teléfono:", self.txt_phone)
        form.addRow("Rol:", self.cb_role)
        form.addRow("Foto Perfil:", self.btn_photo)

        btn_save_user = QPushButton("REGISTRAR USUARIO")
        btn_save_user.clicked.connect(self.save_user)

        form_layout.addLayout(form)
        form_layout.addWidget(btn_save_store)
        form_layout.addSpacing(10)
        form_layout.addWidget(btn_save_user)

        layout.addLayout(form_layout, stretch=1)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("USUARIOS REGISTRADOS"))

        self.table_users = QTableWidget()
        self.table_users.setColumnCount(5)
        self.table_users.setHorizontalHeaderLabels(["ID", "Usuario", "Nombre", "Rol", "Acciones"])
        right_layout.addWidget(self.table_users)

        layout.addLayout(right_layout, stretch=2)

        self.load_store_info()
        self.load_users()

    def select_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Foto", "", "Imágenes (*.png *.jpg *.jpeg)")
        if file_path:
            uid = str(uuid.uuid4())[:8]
            dest = os.path.join(UPLOADS_DIR, f"user_{uid}.jpg")
            process_and_crop_square(file_path, dest, size=150)
            self.photo_path = dest
            self.btn_photo.setText("Foto Lista ✓")

    def reset_user_form(self):
        self.txt_user.clear()
        self.txt_pass.clear()
        self.txt_pass_confirm.clear()
        self.txt_name.clear()
        self.txt_ci.clear()
        self.txt_address.clear()
        self.txt_phone.clear()
        self.photo_path = ""
        self.btn_photo.setText("Subir Foto Perfil")

    def save_store_info(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO store_info (id, name, address, phone) VALUES (1, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET name=excluded.name, address=excluded.address, phone=excluded.phone
        """, (self.txt_store_name.text(), self.txt_store_address.text(), self.txt_store_phone.text()))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Éxito", "Datos del negocio actualizados.")

    def load_store_info(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, address, phone FROM store_info WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            self.txt_store_name.setText(row[0])
            self.txt_store_address.setText(row[1])
            self.txt_store_phone.setText(row[2])

    def save_user(self):
        username = self.txt_user.text().strip()
        password = self.txt_pass.text().strip()
        confirm_password = self.txt_pass_confirm.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Atención", "Complete el usuario y la contraseña.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Error de Validación", "Las contraseñas no coinciden.")
            return

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (username, password, full_name, ci, address, phone, role, photo_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (username, password, self.txt_name.text().strip(),
                  self.txt_ci.text().strip(), self.txt_address.text().strip(), 
                  self.txt_phone.text().strip(), self.cb_role.currentText(), self.photo_path))
            conn.commit()
            QMessageBox.information(self, "Éxito", "Usuario creado correctamente.")
            self.reset_user_form()
            self.load_users()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear usuario: {e}")
        finally:
            conn.close()

    def load_users(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, full_name, role, ci, address, phone FROM users")
        rows = cursor.fetchall()
        conn.close()

        self.table_users.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            uid, uname, fname, role, ci, addr, phone = row
            self.table_users.setItem(r_idx, 0, QTableWidgetItem(str(uid)))
            self.table_users.setItem(r_idx, 1, QTableWidgetItem(uname))
            self.table_users.setItem(r_idx, 2, QTableWidgetItem(fname))
            self.table_users.setItem(r_idx, 3, QTableWidgetItem(role))

            btn_box = QWidget()
            box_layout = QHBoxLayout()
            box_layout.setContentsMargins(0, 0, 0, 0)
            btn_box.setLayout(box_layout)

            btn_edit = QPushButton("Editar / Pass")
            u_data = {'id': uid, 'username': uname, 'full_name': fname, 'role': role, 'ci': ci, 'address': addr, 'phone': phone}
            btn_edit.clicked.connect(lambda _, d=u_data: self.edit_user(d))

            btn_del = QPushButton("Eliminar")
            btn_del.setObjectName("btn_danger")
            btn_del.clicked.connect(lambda _, u=uid: self.delete_user(u))

            box_layout.addWidget(btn_edit)
            box_layout.addWidget(btn_del)

            self.table_users.setCellWidget(r_idx, 4, btn_box)

    def edit_user(self, user_data):
        dlg = EditUserDialog(user_data, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_users()

    def delete_user(self, user_id):
        confirm = QMessageBox.question(self, "Confirmar", "¿Eliminar este usuario?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            self.load_users()