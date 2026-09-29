from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, 
                             QCheckBox, QDoubleSpinBox, QPushButton, QFileDialog, 
                             QHBoxLayout, QMessageBox, QDateEdit, QScrollArea, 
                             QFrame, QLabel, QGridLayout, QDialog, QListWidget)
from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from database import get_connection
from utils.image_utils import process_and_crop_square
import uuid
import os
from config import UPLOADS_DIR

class EditProductDialog(QDialog):
    def __init__(self, prod_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Producto")
        self.setMinimumWidth(350)
        self.prod_id = prod_data[0]

        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()
        self.txt_name = QLineEdit(prod_data[1])
        self.txt_brand = QLineEdit(prod_data[2])
        self.txt_unit = QLineEdit(prod_data[3])
        self.spn_min_stock = QDoubleSpinBox()
        self.spn_min_stock.setMaximum(999999)
        self.spn_min_stock.setValue(prod_data[4])
        self.spn_sale_price = QDoubleSpinBox()
        self.spn_sale_price.setMaximum(999999)
        self.spn_sale_price.setValue(prod_data[5])

        form.addRow("Nombre:", self.txt_name)
        form.addRow("Marca:", self.txt_brand)
        form.addRow("Unidad Medida:", self.txt_unit)
        form.addRow("Stock Mínimo (Alerta):", self.spn_min_stock)
        form.addRow("Precio Venta ($):", self.spn_sale_price)

        layout.addLayout(form)

        btn_save = QPushButton("GUARDAR CAMBIOS")
        btn_save.clicked.connect(self.save)
        layout.addWidget(btn_save)

    def save(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE products 
            SET name = ?, brand = ?, unit_type = ?, min_stock = ?, sale_price = ?
            WHERE id = ?
        """, (self.txt_name.text().strip(), self.txt_brand.text().strip(), 
              self.txt_unit.text().strip(), self.spn_min_stock.value(), 
              self.spn_sale_price.value(), self.prod_id))
        conn.commit()
        conn.close()
        self.accept()


class AlmacenWidget(QWidget):
    product_updated_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        self.setLayout(layout)

        cat_box = QVBoxLayout()
        cat_box.addWidget(QLabel("CATEGORÍAS"))
        self.txt_cat_name = QLineEdit()
        self.txt_cat_name.setPlaceholderText("Nueva categoría...")
        btn_add_cat = QPushButton("Crear Categoría")
        btn_add_cat.clicked.connect(self.create_category)

        self.list_cats = QListWidget()

        cat_box.addWidget(self.txt_cat_name)
        cat_box.addWidget(btn_add_cat)
        cat_box.addWidget(self.list_cats)
        layout.addLayout(cat_box, stretch=1)

        form_layout = QVBoxLayout()
        form = QFormLayout()

        self.txt_name = QLineEdit()
        self.txt_brand = QLineEdit()
        self.cb_cat = QComboBox()
        self.chk_edible = QCheckBox("Es Comestible")
        self.txt_unit = QLineEdit()
        self.txt_unit.setPlaceholderText("Ej: Latas, Cajas, Paquetes")
        self.date_expiry = QDateEdit(QDate.currentDate())
        self.spn_initial_stock = QDoubleSpinBox()
        self.spn_initial_stock.setMaximum(999999)
        
        self.spn_min_stock = QDoubleSpinBox()
        self.spn_min_stock.setMaximum(999999)
        self.spn_min_stock.setValue(5.0)

        self.txt_barcode = QLineEdit()

        self.btn_photo = QPushButton("Subir Foto Producto")
        self.btn_photo.clicked.connect(self.select_photo)
        self.photo_path = ""

        form.addRow("Nombre Producto:", self.txt_name)
        form.addRow("Marca / Sabor:", self.txt_brand)
        form.addRow("Categoría:", self.cb_cat)
        form.addRow("Comestible:", self.chk_edible)
        form.addRow("Unidad de Medida:", self.txt_unit)
        form.addRow("Vencimiento:", self.date_expiry)
        form.addRow("Stock Inicial:", self.spn_initial_stock)
        form.addRow("Stock Mínimo:", self.spn_min_stock)
        form.addRow("Código de Barras:", self.txt_barcode)
        form.addRow("Foto:", self.btn_photo)

        btn_add = QPushButton("REGISTRAR EN ALMACÉN")
        btn_add.clicked.connect(self.save_product)

        form_layout.addLayout(form)
        form_layout.addWidget(btn_add)
        layout.addLayout(form_layout, stretch=2)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("INVENTARIO EN ALMACÉN"))

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.prod_container = QWidget()
        self.prod_grid = QGridLayout()
        self.prod_container.setLayout(self.prod_grid)
        self.scroll_area.setWidget(self.prod_container)

        right_layout.addWidget(self.scroll_area)
        layout.addLayout(right_layout, stretch=3)

        self.load_categories()
        self.load_products_cards()

    def create_category(self):
        cat_name = self.txt_cat_name.text().strip()
        if not cat_name:
            return
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat_name,))
            conn.commit()
            self.txt_cat_name.clear()
            self.load_categories()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo crear la categoría: {e}")
        finally:
            conn.close()

    def select_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Foto", "", "Imágenes (*.png *.jpg *.jpeg)")
        if file_path:
            uid = str(uuid.uuid4())[:8]
            dest = os.path.join(UPLOADS_DIR, f"prod_{uid}.jpg")
            process_and_crop_square(file_path, dest, size=200)
            self.photo_path = dest
            self.btn_photo.setText("Foto Lista ✓")

    def reset_form(self):
        self.txt_name.clear()
        self.txt_brand.clear()
        self.txt_unit.clear()
        self.txt_barcode.clear()
        self.spn_initial_stock.setValue(0.0)
        self.spn_min_stock.setValue(5.0)
        self.photo_path = ""
        self.btn_photo.setText("Subir Foto Producto")

    def load_categories(self):
        self.cb_cat.clear()
        self.list_cats.clear()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM categories")
        rows = cursor.fetchall()
        for cid, name in rows:
            self.cb_cat.addItem(name, cid)
            self.list_cats.addItem(name)
        conn.close()

    def save_product(self):
        if not self.txt_name.text().strip() or not self.txt_unit.text().strip():
            QMessageBox.warning(self, "Atención", "Complete Nombre y Unidad de Medida.")
            return

        conn = get_connection()
        cursor = conn.cursor()
        prod_id = f"PRD-{str(uuid.uuid4())[:8].upper()}"
        cat_id = self.cb_cat.currentData()

        cursor.execute("""
            INSERT INTO products (id, name, brand, category_id, is_edible, unit_type, expiry_date, entry_date, photo_path, barcode, stock, min_stock, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, DATE('now'), ?, ?, ?, ?, 1)
        """, (prod_id, self.txt_name.text().strip(), self.txt_brand.text().strip(), cat_id,
              1 if self.chk_edible.isChecked() else 0, self.txt_unit.text().strip(),
              self.date_expiry.date().toString("yyyy-MM-dd"), self.photo_path,
              self.txt_barcode.text().strip(), self.spn_initial_stock.value(), self.spn_min_stock.value()))

        conn.commit()
        conn.close()

        QMessageBox.information(self, "Éxito", f"Producto Creado: {prod_id}")
        self.reset_form()
        self.load_products_cards()
        self.product_updated_signal.emit()

    def load_products_cards(self):
        for i in reversed(range(self.prod_grid.count())): 
            widget = self.prod_grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, brand, unit_type, stock, min_stock, photo_path, sale_price FROM products WHERE active = 1")
        products = cursor.fetchall()
        conn.close()

        cols = 2
        for idx, (pid, name, brand, unit_type, stock, min_stock, photo, price) in enumerate(products):
            card = QFrame()
            is_low = stock <= min_stock
            card.setProperty("class", "MiniCardAlert" if is_low else "MiniCard")
            
            card_layout = QVBoxLayout()
            card_layout.setContentsMargins(5, 5, 5, 5)
            card.setLayout(card_layout)

            top_h = QHBoxLayout()
            lbl_img = QLabel()
            lbl_img.setFixedSize(45, 45)
            if photo and os.path.exists(photo):
                pixmap = QPixmap(photo)
            else:
                pixmap = QPixmap(45, 45)
                pixmap.fill(Qt.GlobalColor.darkRed if is_low else Qt.GlobalColor.darkGray)
            lbl_img.setPixmap(pixmap.scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            top_h.addWidget(lbl_img)

            info = QVBoxLayout()
            info.setSpacing(1)
            display_title = f"{name} ({brand})" if brand else name
            info.addWidget(QLabel(f"<b>{display_title}</b>"))
            stock_color = "#ff0055" if is_low else "#00f0ff"
            info.addWidget(QLabel(f"Stock: <font color='{stock_color}'><b>{stock} {unit_type}</b></font>"))
            info.addWidget(QLabel(f"P.Venta: ${price:.2f}"))
            top_h.addLayout(info)

            card_layout.addLayout(top_h)

            act_h = QHBoxLayout()
            btn_edit = QPushButton("Editar")
            btn_edit.clicked.connect(lambda _, p_data=(pid, name, brand, unit_type, min_stock, price): self.edit_product(p_data))

            btn_del = QPushButton("Eliminar")
            btn_del.setObjectName("btn_danger")
            btn_del.clicked.connect(lambda _, p_id=pid: self.delete_product(p_id))

            act_h.addWidget(btn_edit)
            act_h.addWidget(btn_del)
            card_layout.addLayout(act_h)

            row = idx // cols
            col = idx % cols
            self.prod_grid.addWidget(card, row, col)

    def edit_product(self, prod_data):
        dlg = EditProductDialog(prod_data, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_products_cards()
            self.product_updated_signal.emit()

    def delete_product(self, prod_id):
        confirm = QMessageBox.question(self, "Eliminar", f"¿Desea eliminar el producto {prod_id}?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                # Los productos tienen histórico en facturas y ventas. No se elimina
                # físicamente porque eso destruiría la trazabilidad y violaría las FK.
                cursor.execute("UPDATE products SET active = 0 WHERE id = ?", (prod_id,))
                conn.commit()
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Error", f"No se pudo retirar el producto: {e}")
                return
            finally:
                conn.close()
            self.load_products_cards()
            self.product_updated_signal.emit()