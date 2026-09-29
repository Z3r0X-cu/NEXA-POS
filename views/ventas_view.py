from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QDoubleSpinBox, QLabel,
                             QMessageBox, QScrollArea, QFrame, QGridLayout, QDialog,
                             QFormLayout, QComboBox, QLineEdit, QFileDialog)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from database import get_connection
from utils.pdf_generator import generate_receipt_pdf
from config import PDF_DIR, UPLOADS_DIR
from datetime import datetime
import os
import uuid


class PaymentDialog(QDialog):
    def __init__(self, total, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Datos del Pago")
        self.setMinimumWidth(420)
        self.proof_path = ""
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Total a pagar: ${total:.2f}</b>"))
        form = QFormLayout()
        self.cb_method = QComboBox(); self.cb_method.addItems(["EFECTIVO", "TRANSFERENCIA"])
        self.txt_card = QLineEdit(); self.txt_name = QLineEdit(); self.txt_ci = QLineEdit()
        self.txt_phone = QLineEdit(); self.txt_address = QLineEdit()
        self.btn_proof = QPushButton("Adjuntar foto de la transferencia")
        self.btn_proof.clicked.connect(self.select_proof)
        form.addRow("Forma de pago:", self.cb_method)
        form.addRow("Número de tarjeta:", self.txt_card)
        form.addRow("Nombre del pagador:", self.txt_name)
        form.addRow("CI del pagador:", self.txt_ci)
        form.addRow("Teléfono:", self.txt_phone)
        form.addRow("Dirección:", self.txt_address)
        form.addRow("Comprobante:", self.btn_proof)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        ok = QPushButton("CONFIRMAR PAGO"); cancel = QPushButton("CANCELAR")
        ok.clicked.connect(self.accept_payment); cancel.clicked.connect(self.reject)
        buttons.addWidget(ok); buttons.addWidget(cancel); layout.addLayout(buttons)
        self.cb_method.currentTextChanged.connect(self.toggle_transfer_fields)
        self.toggle_transfer_fields(self.cb_method.currentText())

    def toggle_transfer_fields(self, method):
        enabled = method == "TRANSFERENCIA"
        for w in [self.txt_card, self.txt_name, self.txt_ci, self.txt_phone, self.txt_address, self.btn_proof]:
            w.setEnabled(enabled)

    def select_proof(self):
        path, _ = QFileDialog.getOpenFileName(self, "Foto de transferencia", "", "Imágenes (*.png *.jpg *.jpeg)")
        if path:
            dest_dir = os.path.join(UPLOADS_DIR, "transfers"); os.makedirs(dest_dir, exist_ok=True)
            ext = os.path.splitext(path)[1]
            dest = os.path.join(dest_dir, f"transfer_{uuid.uuid4().hex[:10]}{ext}")
            with open(path, 'rb') as src, open(dest, 'wb') as dst: dst.write(src.read())
            self.proof_path = dest; self.btn_proof.setText("Foto lista ✓")

    def accept_payment(self):
        if self.cb_method.currentText() == "TRANSFERENCIA":
            if not self.txt_card.text().strip() or not self.txt_name.text().strip() or not self.proof_path:
                QMessageBox.warning(self, "Datos incompletos", "Para una transferencia debe indicar tarjeta, nombre del pagador y adjuntar la foto de la transacción.")
                return
        self.accept()

    def data(self):
        return {
            'payment_method': self.cb_method.currentText(),
            'payer_card_number': self.txt_card.text().strip(),
            'payer_name': self.txt_name.text().strip(),
            'payer_ci': self.txt_ci.text().strip(),
            'payer_phone': self.txt_phone.text().strip(),
            'payer_address': self.txt_address.text().strip(),
            'transfer_proof_path': self.proof_path,
        }


class VentasWidget(QWidget):
    product_sold_signal = pyqtSignal()

    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data; self.cart = []
        layout = QHBoxLayout(); self.setLayout(layout)
        left_panel = QVBoxLayout(); left_panel.addWidget(QLabel("CATÁLOGO DE PRODUCTOS"))
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.cat_container = QWidget(); self.cat_grid = QGridLayout(); self.cat_container.setLayout(self.cat_grid); self.scroll.setWidget(self.cat_container)
        left_panel.addWidget(self.scroll); layout.addLayout(left_panel, stretch=2)
        right_panel = QVBoxLayout(); right_panel.addWidget(QLabel("CARRITO DE COMPRAS"))
        self.cart_table = QTableWidget(); self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["Foto", "Producto", "Cant.", "Subtotal", "Acción"]); self.cart_table.setIconSize(QSize(35,35))
        right_panel.addWidget(self.cart_table)
        self.lbl_total = QLabel("TOTAL: $0.00"); self.lbl_total.setStyleSheet("font-size: 22px; color: #00f0ff; font-weight: bold;"); right_panel.addWidget(self.lbl_total)
        btn_checkout = QPushButton("PROCESAR VENTA"); btn_checkout.setStyleSheet("background-color: #ff0055; color: white; padding: 10px; font-size: 14px;"); btn_checkout.clicked.connect(self.process_sale); right_panel.addWidget(btn_checkout)
        layout.addLayout(right_panel, stretch=1)
        self.load_catalog_cards()

    def load_catalog_cards(self):
        for i in reversed(range(self.cat_grid.count())):
            widget = self.cat_grid.itemAt(i).widget()
            if widget: widget.deleteLater()
        conn = get_connection(); cursor = conn.cursor()
        cursor.execute("SELECT id, name, brand, stock, min_stock, unit_type, sale_price, purchase_price, photo_path FROM products WHERE active=1 AND stock>0 ORDER BY name")
        products = cursor.fetchall(); conn.close()
        for idx, (pid,name,brand,stock,min_stock,unit_type,price,cost,photo) in enumerate(products):
            card=QFrame(); card.setProperty("class", "MiniCardAlert" if stock<=min_stock else "MiniCard")
            card_layout=QVBoxLayout(); card_layout.setContentsMargins(5,5,5,5); card.setLayout(card_layout)
            lbl_img=QLabel(); lbl_img.setFixedSize(50,50)
            if photo and os.path.exists(photo): pixmap=QPixmap(photo)
            else: pixmap=QPixmap(50,50); pixmap.fill(Qt.GlobalColor.darkBlue)
            lbl_img.setPixmap(pixmap.scaled(50,50,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)); card_layout.addWidget(lbl_img,alignment=Qt.AlignmentFlag.AlignCenter)
            title=f"{name} ({brand})" if brand else name; card_layout.addWidget(QLabel(f"<b>{title}</b>")); card_layout.addWidget(QLabel(f"Precio: <font color='#00f0ff'>${price:.2f}</font>"))
            stock_lbl=QLabel(f"⚠️ ¡QUEDAN {stock} {unit_type}!" if stock<=min_stock else f"Stock: {stock} {unit_type}"); stock_lbl.setStyleSheet("color:#ff0055;font-weight:bold;" if stock<=min_stock else "color:#aaaaaa;"); card_layout.addWidget(stock_lbl)
            spn_qty=QDoubleSpinBox(); spn_qty.setMinimum(0.01); spn_qty.setMaximum(stock); spn_qty.setValue(1.0)
            btn_add=QPushButton("Añadir"); btn_add.clicked.connect(lambda _,p=pid,n=title,pr=price,c=cost,st=stock,u=unit_type,ph=photo,s=spn_qty:self.add_to_cart(p,n,pr,c,st,u,ph,s.value()))
            actions=QHBoxLayout(); actions.addWidget(spn_qty); actions.addWidget(btn_add); card_layout.addLayout(actions)
            self.cat_grid.addWidget(card, idx//3, idx%3)

    def add_to_cart(self,pid,name,price,cost,stock,unit_type,photo,qty):
        for idx,item in enumerate(self.cart):
            if item[0]==pid:
                new_qty=item[2]+qty
                if new_qty>stock: QMessageBox.warning(self,"Límite Superado",f"No puedes agregar más de {stock} {unit_type}."); return
                self.cart[idx]=(pid,name,new_qty,price,new_qty*price,new_qty*cost,photo,stock,unit_type); self.update_cart_ui(); return
        self.cart.append((pid,name,qty,price,qty*price,qty*cost,photo,stock,unit_type)); self.update_cart_ui()

    def remove_from_cart(self,index): self.cart.pop(index); self.update_cart_ui()

    def update_cart_ui(self):
        self.cart_table.setRowCount(len(self.cart)); total=0.0
        for r,item in enumerate(self.cart):
            pid,name,qty,price,subtotal,_,photo,_,unit_type=item; total+=subtotal
            lbl=QLabel(); lbl.setFixedSize(30,30)
            pix=QPixmap(photo) if photo and os.path.exists(photo) else QPixmap(30,30)
            if pix.isNull(): pix.fill(Qt.GlobalColor.darkGray)
            lbl.setPixmap(pix.scaled(30,30,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
            self.cart_table.setCellWidget(r,0,lbl); self.cart_table.setItem(r,1,QTableWidgetItem(name)); self.cart_table.setItem(r,2,QTableWidgetItem(f"{qty} {unit_type}")); self.cart_table.setItem(r,3,QTableWidgetItem(f"${subtotal:.2f}"))
            btn=QPushButton("Quitar"); btn.setObjectName("btn_danger"); btn.clicked.connect(lambda _,pos=r:self.remove_from_cart(pos)); self.cart_table.setCellWidget(r,4,btn)
        self.lbl_total.setText(f"TOTAL: ${total:.2f}")

    def _allocate_costs(self, cursor, pid, qty, fallback_cost):
        remaining=qty; allocations=[]
        cursor.execute("SELECT id, remaining_quantity, purchase_price FROM invoices WHERE product_id=? AND remaining_quantity>0 ORDER BY id", (pid,))
        for inv_id, available, cost in cursor.fetchall():
            if remaining<=0: break
            take=min(remaining,float(available)); allocations.append((inv_id,take,float(cost)))
            remaining-=take
        if remaining>1e-9: allocations.append((None,remaining,float(fallback_cost)))
        return allocations

    def process_sale(self):
        if not self.cart: QMessageBox.warning(self,"Atención","El carrito está vacío."); return
        total=sum(item[4] for item in self.cart)
        payment_dialog=PaymentDialog(total,self)
        if payment_dialog.exec()!=QDialog.DialogCode.Accepted: return
        payment=payment_dialog.data()

        conn=get_connection(); cursor=conn.cursor()
        try:
            # Verificación de stock justo antes de confirmar la operación.
            for item in self.cart:
                cursor.execute("SELECT stock FROM products WHERE id=? AND active=1",(item[0],)); row=cursor.fetchone()
                if not row or float(row[0])+1e-9<item[2]: raise ValueError(f"Stock insuficiente para {item[1]}.")

            allocations_by_item=[]; total_cost=0.0
            for item in self.cart:
                allocations=self._allocate_costs(cursor,item[0],item[2],item[5]/item[2] if item[2] else 0)
                allocations_by_item.append((item,allocations)); total_cost += sum(q*cost for _,q,cost in allocations)

            cursor.execute("""
                INSERT INTO sales (seller_id,total_amount,total_cost,date,payment_method,transfer_proof_path,
                                   payer_card_number,payer_name,payer_ci,payer_phone,payer_address)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,(self.user_data['id'],total,total_cost,datetime.now().strftime('%Y-%m-%d %H:%M:%S'),payment['payment_method'],payment['transfer_proof_path'],payment['payer_card_number'],payment['payer_name'],payment['payer_ci'],payment['payer_phone'],payment['payer_address']))
            sale_id=cursor.lastrowid; pdf_items=[]
            for item,allocations in allocations_by_item:
                pid,name,qty,price,subtotal,*_=item
                for inv_id,take,cost in allocations:
                    cursor.execute("INSERT INTO sale_details (sale_id,product_id,quantity,unit_price,unit_cost,invoice_id) VALUES (?,?,?,?,?,?)",(sale_id,pid,take,price,cost,inv_id))
                    if inv_id is not None:
                        cursor.execute("UPDATE invoices SET remaining_quantity=remaining_quantity-? WHERE id=?",(take,inv_id))
                cursor.execute("UPDATE products SET stock=stock-? WHERE id=?",(qty,pid))
                pdf_items.append((name,qty,price,subtotal))
            conn.commit()
        except Exception as e:
            conn.rollback(); conn.close(); QMessageBox.critical(self,"Error en venta",str(e)); return
        conn.close()

        conn=get_connection(); cursor=conn.cursor(); cursor.execute("SELECT name,address,phone FROM store_info WHERE id=1"); st=cursor.fetchone(); conn.close()
        store_info={'name':st[0] if st else 'Mi POS','address':st[1] if st else '','phone':st[2] if st else ''}
        time_stamp=datetime.now().strftime('%Y%m%d_%H%M%S'); full_pdf_path=os.path.join(PDF_DIR,f"comprobante_{time_stamp}_FAC{sale_id:06d}.pdf")
        generate_receipt_pdf(full_pdf_path,store_info,sale_id,self.user_data['full_name'],pdf_items,total,payment)
        QMessageBox.information(self,"Venta Exitosa",f"Venta #{sale_id} Procesada.\nComprobante guardado en:\n{full_pdf_path}")
        self.cart.clear(); self.update_cart_ui(); self.load_catalog_cards(); self.product_sold_signal.emit()
