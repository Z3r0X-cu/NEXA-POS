import sqlite3
import shutil
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def _add_column(cursor, table, column, definition):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    except sqlite3.OperationalError:
        pass


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS store_info (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        name TEXT NOT NULL, address TEXT NOT NULL, phone TEXT NOT NULL,
        socials TEXT, website TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, full_name TEXT NOT NULL, ci TEXT NOT NULL,
        address TEXT NOT NULL, phone TEXT NOT NULL,
        role TEXT CHECK(role IN ('admin','almacenero','economia','vendedor')) NOT NULL,
        photo_path TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, brand TEXT NOT NULL, category_id INTEGER,
        is_edible INTEGER NOT NULL, unit_type TEXT NOT NULL, expiry_date TEXT,
        entry_date TEXT NOT NULL, photo_path TEXT, barcode TEXT, stock REAL DEFAULT 0,
        min_stock REAL DEFAULT 5.0, purchase_price REAL DEFAULT 0.0,
        sale_price REAL DEFAULT 0.0, active INTEGER DEFAULT 1,
        FOREIGN KEY(category_id) REFERENCES categories(id)
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_number TEXT NOT NULL,
        product_id TEXT NOT NULL, purchase_price REAL NOT NULL, sale_price REAL NOT NULL,
        quantity REAL NOT NULL, supplier TEXT, proof_path TEXT, date TEXT NOT NULL,
        remaining_quantity REAL,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT, seller_id INTEGER NOT NULL,
        total_amount REAL NOT NULL, total_cost REAL NOT NULL, date TEXT NOT NULL,
        payment_method TEXT DEFAULT 'EFECTIVO', transfer_proof_path TEXT,
        payer_card_number TEXT, payer_name TEXT, payer_ci TEXT, payer_phone TEXT,
        payer_address TEXT,
        FOREIGN KEY(seller_id) REFERENCES users(id)
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sale_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sale_id INTEGER NOT NULL,
        product_id TEXT NOT NULL, quantity REAL NOT NULL, unit_price REAL NOT NULL,
        unit_cost REAL NOT NULL, invoice_id INTEGER,
        FOREIGN KEY(sale_id) REFERENCES sales(id),
        FOREIGN KEY(product_id) REFERENCES products(id),
        FOREIGN KEY(invoice_id) REFERENCES invoices(id)
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_closes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, close_date TEXT UNIQUE NOT NULL,
        total_sales REAL NOT NULL, total_profit REAL NOT NULL, sale_count INTEGER NOT NULL,
        receipt_numbers TEXT, pdf_path TEXT, created_at TEXT NOT NULL
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS monthly_closes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, year_month TEXT UNIQUE NOT NULL,
        total_sales REAL NOT NULL, total_profit REAL NOT NULL, total_entries REAL NOT NULL,
        total_purchases REAL NOT NULL, daily_close_count INTEGER NOT NULL,
        pdf_path TEXT, created_at TEXT NOT NULL
    )""")

    # Compatibilidad con bases creadas por NEXA 2.x/3.0 inicial.
    _add_column(cursor, 'products', 'unit_type', "TEXT DEFAULT 'unidades'")
    _add_column(cursor, 'products', 'min_stock', "REAL DEFAULT 5.0")
    _add_column(cursor, 'products', 'active', "INTEGER DEFAULT 1")
    _add_column(cursor, 'invoices', 'supplier', "TEXT")
    _add_column(cursor, 'invoices', 'proof_path', "TEXT")
    _add_column(cursor, 'invoices', 'remaining_quantity', "REAL")
    _add_column(cursor, 'sales', 'payment_method', "TEXT DEFAULT 'EFECTIVO'")
    _add_column(cursor, 'sales', 'transfer_proof_path', "TEXT")
    _add_column(cursor, 'sales', 'payer_card_number', "TEXT")
    _add_column(cursor, 'sales', 'payer_name', "TEXT")
    _add_column(cursor, 'sales', 'payer_ci', "TEXT")
    _add_column(cursor, 'sales', 'payer_phone', "TEXT")
    _add_column(cursor, 'sales', 'payer_address', "TEXT")
    _add_column(cursor, 'sale_details', 'invoice_id', "INTEGER")

    cursor.execute("UPDATE products SET active = 1 WHERE active IS NULL")

    # Para instalaciones antiguas, reconstruir cuánto queda disponible de cada factura
    # sin mezclar facturas ni borrar el histórico. Las ventas antiguas no tenían invoice_id,
    # por lo que se distribuyen FIFO únicamente para determinar existencias pendientes.
    old_invoice_rows = cursor.execute("SELECT DISTINCT product_id FROM invoices WHERE remaining_quantity IS NULL").fetchall()
    for (product_id,) in old_invoice_rows:
        sold = cursor.execute("SELECT COALESCE(SUM(quantity),0) FROM sale_details WHERE product_id=?", (product_id,)).fetchone()[0] or 0
        rows = cursor.execute("SELECT id, quantity FROM invoices WHERE product_id=? ORDER BY id", (product_id,)).fetchall()
        pending_sold = float(sold)
        for inv_id, quantity in rows:
            available = float(quantity)
            used = min(available, pending_sold)
            remaining = available - used
            pending_sold -= used
            cursor.execute("UPDATE invoices SET remaining_quantity=? WHERE id=?", (remaining, inv_id))
    cursor.execute("UPDATE invoices SET remaining_quantity = quantity WHERE remaining_quantity IS NULL")
    cursor.execute("UPDATE sales SET payment_method = 'EFECTIVO' WHERE payment_method IS NULL OR payment_method = ''")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_product_remaining ON invoices(product_id, remaining_quantity, id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_closes_date ON daily_closes(close_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_monthly_closes_month ON monthly_closes(year_month)")

    conn.commit()
    conn.close()


def export_database(destination_path):
    shutil.copyfile(DB_PATH, destination_path)


def import_database(source_path):
    shutil.copyfile(source_path, DB_PATH)
