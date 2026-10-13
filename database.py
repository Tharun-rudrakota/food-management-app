import sqlite3
import os
import tempfile
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash

def get_db_path():
    """Returns database path. Uses OS temp dir (/tmp on Vercel) if in serverless or read-only."""
    if os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME') or os.environ.get('LAMBDA_TASK_ROOT'):
        return os.path.join(tempfile.gettempdir(), 'food_nest.db')

    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'food_nest.db')
    try:
        test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.test_write')
        with open(test_file, 'w') as f:
            f.write('')
        if os.path.exists(test_file):
            os.remove(test_file)
        return local_path
    except (OSError, IOError, PermissionError):
        return os.path.join(tempfile.gettempdir(), 'food_nest.db')

def _connect_raw():
    """Internal raw connection without recursive init check."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_db_connection():
    """Returns a SQLite connection with row factory enabled. Initializes schema if missing."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        init_db()
    return _connect_raw()

def init_db():
    """Initializes FreshPantry database schema."""
    conn = _connect_raw()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS food_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        quantity REAL NOT NULL DEFAULT 1.0,
        unit TEXT NOT NULL DEFAULT 'pcs',
        storage_location TEXT NOT NULL DEFAULT 'Fridge',
        purchase_date TEXT NOT NULL,
        expiry_date TEXT NOT NULL,
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS daily_consumption (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        food_id INTEGER NULL,
        food_name TEXT NOT NULL,
        quantity_consumed REAL NOT NULL,
        unit TEXT NOT NULL,
        date_consumed TEXT NOT NULL,
        meal_type TEXT DEFAULT 'Lunch',
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

def get_item_status(expiry_date_str, today=None):
    """Calculates status: 'Expired', 'Expiring Soon', or 'Fresh'."""
    if today is None:
        today = date.today()
    try:
        exp_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return 'Fresh'

    delta_days = (exp_date - today).days

    if delta_days < 0:
        return 'Expired'
    elif 0 <= delta_days <= 7:
        return 'Expiring Soon'
    else:
        return 'Fresh'

def seed_data():
    """No-op: Demo seeding removed. Users register their own accounts."""
    pass

if __name__ == '__main__':
    print("Initializing FreshPantry database...")
    init_db()
    print("FreshPantry database ready!")
