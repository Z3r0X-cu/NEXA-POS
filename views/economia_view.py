from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QComboBox, QDoubleSpinBox, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QMessageBox, QLabel, QFileDialog)
from PyQt6.QtCore import pyqtSignal
from database import get_connection
from utils.pdf_generator import generate_daily_close_pdf, generate_monthly_close_pdf
from config import PDF_DIR, UPLOADS_DIR
from datetime import datetime
import os
import uuid


class EconomiaWidget(QWidget):
    product_updated_signal = pyqtSignal()

    def __init__(self, read_only_inventory=False):
        super().__init__()
        self.read_only = read_only_inventory
        layout = QHBoxLayout()
        self.setLayout(layout)

        form_layout = QVBoxLayout()
        form = QFormLayout()
        self.txt_inv_num = QLineEdit()
        self.cb_products = QComboBox()
        self.spn_purchase_price = QDoubleSpinBox()
        self.spn_purchase_price.setMaximum(999999)
        self.spn_sale_price = QDoubleSpinBox()
        self.spn_sale_price.setMaximum(999999)
        self.spn_qty = QDoubleSpinBox()
        self.spn_qty.setMaximum(999999)
        self.spn_qty.setValue(1.0)
        self.txt_supplier = QLineEdit()
        self.txt_supplier.setPlaceholderText("Empresa / Persona proveedora")
        self.btn_proof = QPushButton("Adjuntar Factura/Comprobante")
        self.btn_proof.clicked.connect(self.select_proof)
        self.proof_path = ""

        form.addRow("No. Factura Entrada:", self.txt_inv_num)
        form.addRow("Producto:", self.cb_products)
        form.addRow("Proveedor / Origen:", self.txt_supplier)
        form.addRow("Precio Compra Unitario ($):", self.spn_purchase_price)
        form.addRow("Precio Venta Unitario ($):", self.spn_sale_price)
        form.addRow("Cantidad Ingresada:", self.spn_qty)
        form.addRow("Foto/Doc Factura:", self.btn_proof)

        btn_add_stock = QPushButton("REGISTRAR ENTRADA DE STOCK")
        btn_add_stock.clicked.connect(self.register_entry)
        btn_close = QPushButton("GENERAR CIERRE DÍA (PDF)")
        btn_close.setStyleSheet("background-color: #ff0055; color: white;")
        btn_close.clicked.connect(self.close_day)
        btn_monthly = QPushButton("GENERAR CUADRE MENSUAL (DÍA 28)")
        btn_monthly.clicked.connect(self.close_month)

        form_layout.addLayout(form)
        form_layout.addWidget(btn_add_stock)
        form_layout.addSpacing(15)
        form_layout.addWidget(btn_close)
        form_layout.addWidget(btn_monthly)
        layout.addLayout(form_layout, stretch=1)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("INVENTARIO GENERAL (VALORIZACIÓN)"))
        self.table_inventory = QTableWidget()
        self.table_inventory.setColumnCount(6)
        self.table_inventory.setHorizontalHeaderLabels(["ID", "Producto", "Stock", "P.Compra", "P.Venta", "Valor Total"])
        right_layout.addWidget(self.table_inventory)
        layout.addLayout(right_layout, stretch=2)

        self.load_products_combo()
        self.refresh_all()

    def select_proof(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Factura/Comprobante", "", "Archivos (*.png *.jpg *.jpeg *.pdf)")
        if file_path:
            ext = os.path.splitext(file_path)[1]
            dest_dir = os.path.join(UPLOADS_DIR, "invoices")
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, f"proof_{str(uuid.uuid4())[:8]}{ext}")
            with open(file_path, 'rb') as src, open(dest, 'wb') as dst:
                dst.write(src.read())
            self.proof_path = dest
            self.btn_proof.setText("Comprobante Listo ✓")

    def reset_form(self):
        self.txt_inv_num.clear()
        self.txt_supplier.clear()
        self.spn_purchase_price.setValue(0.0)
        self.spn_sale_price.setValue(0.0)
        self.spn_qty.setValue(1.0)
        self.proof_path = ""
        self.btn_proof.setText("Adjuntar Factura/Comprobante")

    def load_products_combo(self):
        self.cb_products.clear()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, brand FROM products WHERE active = 1 ORDER BY name")
        for pid, name, brand in cursor.fetchall():
            title = f"{name} ({brand})" if brand else name
            self.cb_products.addItem(f"{pid} - {title}", pid)
        conn.close()

    def register_entry(self):
        pid = self.cb_products.currentData()
        inv_num = self.txt_inv_num.text().strip()
        p_price = self.spn_purchase_price.value()
        s_price = self.spn_sale_price.value()
        qty = self.spn_qty.value()
        supplier = self.txt_supplier.text().strip()
        if not pid or not inv_num or qty <= 0:
            QMessageBox.warning(self, "Atención", "Complete el número de factura, producto y cantidad.")
            return

        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Cada factura siempre queda como una entrada independiente.
            # No se modifica el costo histórico almacenado en products.
            cursor.execute("""
                INSERT INTO invoices
                (invoice_number, product_id, purchase_price, sale_price, quantity,
                 supplier, proof_path, date, remaining_quantity)
                VALUES (?, ?, ?, ?, ?, ?, ?, DATETIME('now'), ?)
            """, (inv_num, pid, p_price, s_price, qty, supplier, self.proof_path, qty))

            # El stock solo aumenta por la cantidad de esta factura.
            # El precio de compra histórico permanece en invoices.
            if s_price > 0:
                cursor.execute("UPDATE products SET stock = stock + ?, sale_price = ? WHERE id = ?",
                               (qty, s_price, pid))
            else:
                cursor.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (qty, pid))
            conn.commit()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", f"No se pudo registrar la entrada: {e}")
            conn.close()
            return
        conn.close()

        QMessageBox.information(self, "Éxito", f"Entrada registrada para {pid}\nFactura: {inv_num}\nCantidad agregada: {qty}")
        self.reset_form()
        self.refresh_all()
        self.product_updated_signal.emit()

    def refresh_all(self):
        self.load_products_combo()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.name, p.brand, p.stock, p.unit_type, p.sale_price,
                   COALESCE((SELECT i.purchase_price FROM invoices i
                             WHERE i.product_id = p.id ORDER BY i.id DESC LIMIT 1), p.purchase_price) AS latest_purchase
            FROM products p WHERE p.active = 1 ORDER BY p.name
        """)
        products = cursor.fetchall()
        conn.close()
        self.table_inventory.setRowCount(len(products))
        for r_idx, (pid, name, brand, stock, unit, s_price, p_price) in enumerate(products):
            title = f"{name} ({brand})" if brand else name
            val_total = stock * s_price
            self.table_inventory.setItem(r_idx, 0, QTableWidgetItem(pid))
            self.table_inventory.setItem(r_idx, 1, QTableWidgetItem(title))
            self.table_inventory.setItem(r_idx, 2, QTableWidgetItem(f"{stock} {unit}"))
            self.table_inventory.setItem(r_idx, 3, QTableWidgetItem(f"${p_price:.2f}"))
            self.table_inventory.setItem(r_idx, 4, QTableWidgetItem(f"${s_price:.2f}"))
            self.table_inventory.setItem(r_idx, 5, QTableWidgetItem(f"${val_total:.2f}"))

    def close_day(self):
        date_str = datetime.now().strftime("%Y-%m-%d")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, address, phone FROM store_info WHERE id = 1")
        st = cursor.fetchone()
        store_info = {'name': st[0] if st else "POS", 'address': st[1] if st else '', 'phone': st[2] if st else ''}

        cursor.execute("""
            SELECT s.id, u.full_name, s.total_amount,
                   (s.total_amount - s.total_cost), strftime('%H:%M', s.date)
            FROM sales s JOIN users u ON s.seller_id = u.id
            WHERE DATE(s.date) = DATE(?) ORDER BY s.id
        """, (date_str,))
        sales_list = cursor.fetchall()
        conn.close()

        tot_sales = sum(x[2] for x in sales_list)
        tot_profit = sum(x[3] for x in sales_list)
        receipt_numbers = ', '.join(f"{x[0]:06d}" for x in sales_list) or 'NINGUNO'

        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = os.path.join(PDF_DIR, f"cierre_{date_str}_{time_stamp}.pdf")
        generate_daily_close_pdf(pdf_path, store_info, date_str, tot_sales, tot_profit, sales_list, receipt_numbers)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO daily_closes (close_date, total_sales, total_profit, sale_count,
                                      receipt_numbers, pdf_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, DATETIME('now'))
            ON CONFLICT(close_date) DO UPDATE SET total_sales=excluded.total_sales,
                total_profit=excluded.total_profit, sale_count=excluded.sale_count,
                receipt_numbers=excluded.receipt_numbers, pdf_path=excluded.pdf_path,
                created_at=excluded.created_at
        """, (date_str, tot_sales, tot_profit, len(sales_list), receipt_numbers, pdf_path))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Cierre Generado", f"Ventas del día: ${tot_sales:.2f}\nGanancia: ${tot_profit:.2f}\nComprobantes: {receipt_numbers}\n\nArchivo:\n{pdf_path}")

    def close_month(self):
        today = datetime.now()
        if today.day != 28:
            QMessageBox.warning(self, "Cuadre mensual", "El cuadre mensual está programado para realizarse el día 28 de cada mes.")
            return
        month = today.strftime("%Y-%m")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, address, phone FROM store_info WHERE id = 1")
        st = cursor.fetchone()
        store_info = {'name': st[0] if st else "POS", 'address': st[1] if st else '', 'phone': st[2] if st else ''}

        cursor.execute("""
            SELECT s.id, DATE(s.date), u.full_name, s.total_amount,
                   (s.total_amount - s.total_cost), s.payment_method
            FROM sales s JOIN users u ON s.seller_id=u.id
            WHERE strftime('%Y-%m', s.date)=? ORDER BY s.id
        """, (month,))
        sales = cursor.fetchall()
        cursor.execute("""
            SELECT close_date, total_sales, total_profit, sale_count, receipt_numbers
            FROM daily_closes WHERE substr(close_date,1,7)=? ORDER BY close_date
        """, (month,))
        daily_closes = cursor.fetchall()
        cursor.execute("""
            SELECT i.invoice_number, DATE(i.date), p.name, p.brand, i.quantity,
                   i.purchase_price, i.sale_price, i.supplier
            FROM invoices i JOIN products p ON p.id=i.product_id
            WHERE strftime('%Y-%m', i.date)=? ORDER BY i.id
        """, (month,))
        entries = cursor.fetchall()
        conn.close()

        total_sales = sum(x[3] for x in sales)
        total_profit = sum(x[4] for x in sales)
        total_entries = sum(x[4] for x in entries)
        total_purchases = sum(x[4] * x[5] for x in entries)
        pdf_path = os.path.join(PDF_DIR, f"cuadre_mensual_{month}.pdf")
        generate_monthly_close_pdf(pdf_path, store_info, month, total_sales, total_profit,
                                   total_purchases, daily_closes, entries, sales)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO monthly_closes (year_month, total_sales, total_profit, total_entries,
                                        total_purchases, daily_close_count, pdf_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, DATETIME('now'))
            ON CONFLICT(year_month) DO UPDATE SET total_sales=excluded.total_sales,
                total_profit=excluded.total_profit, total_entries=excluded.total_entries,
                total_purchases=excluded.total_purchases, daily_close_count=excluded.daily_close_count,
                pdf_path=excluded.pdf_path, created_at=excluded.created_at
        """, (month, total_sales, total_profit, total_entries, total_purchases,
              len(daily_closes), pdf_path))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Cuadre Mensual", f"Mes: {month}\nVentas: ${total_sales:.2f}\nGanancia: ${total_profit:.2f}\nCompras registradas: ${total_purchases:.2f}\n\nArchivo:\n{pdf_path}")
