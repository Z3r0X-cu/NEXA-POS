from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from datetime import datetime
from config import LOGO_PATH, APP_NAME, APP_VERSION, APP_AUTHOR, APP_GITHUB_URL
import os


def _header(c, store_info, title):
    width, height = letter
    c.setFillColor(colors.HexColor("#0d0f18"))
    c.rect(0, height - 90, width, 90, fill=1)
    if os.path.exists(LOGO_PATH):
        try:
            c.drawImage(ImageReader(LOGO_PATH), width - 90, height - 78, 55, 55, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    c.setFillColor(colors.HexColor("#00f0ff"))
    c.setFont("Helvetica-Bold", 17)
    c.drawString(40, height - 32, store_info.get('name', APP_NAME).upper())
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 9)
    c.drawString(40, height - 49, f"{store_info.get('address', '')} | Tel: {store_info.get('phone', '')}")
    c.drawString(40, height - 64, f"{title} | NEXA POS v{APP_VERSION}")
    c.setFillColor(colors.HexColor("#ff0055"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, height - 80, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return height - 115


def generate_receipt_pdf(filepath, store_info, sale_id, seller_name, items, total, payment_info=None):
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    y = _header(c, store_info, f"COMPROBANTE DE VENTA #{sale_id:06d}")
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, f"Vendedor: {seller_name}")
    y -= 25
    c.setFillColor(colors.HexColor("#1a1c29"))
    c.rect(40, y - 5, 530, 20, fill=1)
    c.setFillColor(colors.HexColor("#00f0ff"))
    c.setFont("Helvetica-Bold", 10)
    for x, label in [(50, 'Producto'), (280, 'Cant.'), (380, 'P. Unit'), (480, 'Subtotal')]:
        c.drawString(x, y, label)
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    for prod_name, qty, price, subtotal in items:
        y -= 20
        if y < 80:
            c.showPage(); y = height - 50
        c.drawString(50, y, str(prod_name)[:35])
        c.drawString(280, y, str(qty))
        c.drawString(380, y, f"${price:.2f}")
        c.drawString(480, y, f"${subtotal:.2f}")

    y -= 25
    c.setStrokeColor(colors.HexColor("#00f0ff")); c.line(40, y + 10, 570, y + 10)
    c.setFont("Helvetica-Bold", 14); c.setFillColor(colors.HexColor("#ff0055"))
    c.drawString(380, y, f"TOTAL: ${total:.2f}")

    if payment_info:
        y -= 35
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, f"Forma de pago: {payment_info.get('payment_method', 'EFECTIVO')}")
        if payment_info.get('payment_method') == 'TRANSFERENCIA':
            c.setFont("Helvetica", 9)
            y -= 15; c.drawString(40, y, f"Tarjeta: {payment_info.get('payer_card_number', '')}")
            y -= 13; c.drawString(40, y, f"Pagador: {payment_info.get('payer_name', '')} | CI: {payment_info.get('payer_ci', '')}")
            y -= 13; c.drawString(40, y, f"Teléfono: {payment_info.get('payer_phone', '')} | Dirección: {payment_info.get('payer_address', '')}")
            if payment_info.get('transfer_proof_path'):
                y -= 13; c.drawString(40, y, "Comprobante de transferencia: adjunto en el registro digital.")
    c.save()


def generate_daily_close_pdf(filepath, store_info, date_str, total_sales, total_profit, sales_list, receipt_numbers):
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    y = _header(c, store_info, f"CIERRE DE CAJA - {date_str}")
    c.setFillColor(colors.HexColor("#ff0055")); c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, f"TOTAL VENDIDO: ${total_sales:.2f}    |    GANANCIA: ${total_profit:.2f}")
    y -= 28
    c.setFillColor(colors.HexColor("#1a1c29")); c.rect(40, y - 5, 530, 20, fill=1)
    c.setFillColor(colors.HexColor("#00f0ff")); c.setFont("Helvetica-Bold", 9)
    for x, label in [(50,'Comprobante'),(145,'Hora'),(205,'Vendedor'),(385,'Venta'),(480,'Ganancia')]: c.drawString(x,y,label)
    c.setFillColor(colors.black); c.setFont("Helvetica",9)
    for sale_id, seller, amount, profit, stime in sales_list:
        y -= 18
        if y < 55:
            c.showPage(); y = height - 55
        c.drawString(50,y,f"#{sale_id:06d}"); c.drawString(145,y,str(stime)); c.drawString(205,y,str(seller)[:27])
        c.drawString(385,y,f"${amount:.2f}"); c.drawString(480,y,f"${profit:.2f}")
    y -= 28
    if y < 80: c.showPage(); y = height - 55
    c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 10)
    c.drawString(40,y,"NÚMEROS DE COMPROBANTES EMITIDOS:")
    y -= 16; c.setFont("Helvetica",9); c.drawString(40,y,str(receipt_numbers))
    c.save()


def generate_monthly_close_pdf(filepath, store_info, month, total_sales, total_profit,
                               total_purchases, daily_closes, entries, sales):
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    y = _header(c, store_info, f"CUADRE MENSUAL - {month}")
    c.setFillColor(colors.HexColor("#ff0055")); c.setFont("Helvetica-Bold", 12)
    c.drawString(40,y,f"VENTAS: ${total_sales:.2f} | GANANCIA: ${total_profit:.2f} | COMPRAS: ${total_purchases:.2f}")

    y -= 30
    c.setFillColor(colors.HexColor("#00f0ff")); c.setFont("Helvetica-Bold", 11); c.drawString(40,y,"VENTAS DIARIAS")
    y -= 17; c.setFillColor(colors.black); c.setFont("Helvetica",8)
    for sale_id, date, seller, amount, profit, method in sales:
        if y < 55: c.showPage(); y = height - 55
        c.drawString(40,y,f"#{sale_id:06d} {date} {str(seller)[:24]}")
        c.drawString(330,y,f"${amount:.2f}"); c.drawString(410,y,f"Gan. ${profit:.2f}"); c.drawString(500,y,str(method))
        y -= 13

    y -= 10
    if y < 100: c.showPage(); y = height - 55
    c.setFillColor(colors.HexColor("#00f0ff")); c.setFont("Helvetica-Bold", 11); c.drawString(40,y,"CUADRES DIARIOS")
    y -= 17; c.setFillColor(colors.black); c.setFont("Helvetica",8)
    for close_date, sales_total, profit, count, receipts in daily_closes:
        if y < 55: c.showPage(); y = height - 55
        c.drawString(40,y,f"{close_date} | ventas ${sales_total:.2f} | gan. ${profit:.2f} | comprobantes {count}")
        y -= 13

    y -= 10
    if y < 100: c.showPage(); y = height - 55
    c.setFillColor(colors.HexColor("#00f0ff")); c.setFont("Helvetica-Bold", 11); c.drawString(40,y,"ENTRADAS DE STOCK / FACTURAS")
    y -= 17; c.setFillColor(colors.black); c.setFont("Helvetica",8)
    for inv, date, name, brand, qty, pprice, sprice, supplier in entries:
        if y < 55: c.showPage(); y = height - 55
        c.drawString(40,y,f"{inv} {date} {str(name)[:22]} {str(brand)[:14]}")
        c.drawString(315,y,f"Cant. {qty}"); c.drawString(380,y,f"Compra ${pprice:.2f}"); c.drawString(460,y,f"Venta ${sprice:.2f}")
        y -= 13
    c.save()
