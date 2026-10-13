import sqlite3
import os
import tempfile
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash

def get_db_path():
    """Returns database path. Uses OS temp dir (/tmp on Vercel) if VERCEL is set."""
    if os.environ.get('VERCEL'):
        return os.path.join(tempfile.gettempdir(), 'food_nest.db')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'food_nest.db')

def _connect_raw():
    """Internal raw connection without recursive init check."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_db_connection():
    """Returns a SQLite connection with row factory enabled. Auto-seeds if missing."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        init_db()
        seed_data()
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
    """Seeds demo user and initial food inventory items if empty."""
    conn = _connect_raw()
    cursor = conn.cursor()

    # Create demo user if not exists
    cursor.execute("SELECT id FROM users WHERE username = 'demo'")
    user = cursor.fetchone()
    if not user:
        hashed_pw = generate_password_hash('demo123')
        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        """, ('demo', 'demo@foodnest.com', hashed_pw))
        user_id = cursor.lastrowid
    else:
        user_id = user['id']

    # Seed sample food inventory for demo user if none exists
    cursor.execute("SELECT COUNT(*) as count FROM food_inventory WHERE user_id = ?", (user_id,))
    if cursor.fetchone()['count'] == 0:
        today = date.today()

        sample_foods = [
            # Fresh Items (> 7 days remaining)
            ("Farm Fresh Eggs", "Dairy & Eggs", 12.0, "pcs", "Fridge", (today - timedelta(days=2)).isoformat(), (today + timedelta(days=14)).isoformat(), "Organic brown eggs"),
            ("Basmati White Rice", "Grains & Pasta", 2.0, "kg", "Pantry", (today - timedelta(days=10)).isoformat(), (today + timedelta(days=120)).isoformat(), "Sealed bag in pantry"),
            ("Greek Yogurt", "Dairy & Eggs", 500.0, "g", "Fridge", (today - timedelta(days=1)).isoformat(), (today + timedelta(days=10)).isoformat(), "Plain whole milk yogurt"),
            ("Chicken Breast Fillets", "Meat & Seafood", 800.0, "g", "Freezer", (today - timedelta(days=3)).isoformat(), (today + timedelta(days=45)).isoformat(), "Vacuum sealed in freezer"),
            ("Rolled Oats", "Grains & Pasta", 1.0, "kg", "Pantry", (today - timedelta(days=7)).isoformat(), (today + timedelta(days=90)).isoformat(), "Airtight container"),
            ("Extra Virgin Olive Oil", "Condiments & Oils", 1.0, "bottle", "Pantry", (today - timedelta(days=15)).isoformat(), (today + timedelta(days=200)).isoformat(), "Dark glass bottle"),
            ("Crisp Fuji Apples", "Fruits", 6.0, "pcs", "Fridge", (today - timedelta(days=2)).isoformat(), (today + timedelta(days=12)).isoformat(), "Crisper drawer"),

            # Expiring Soon Items (within 0 - 7 days)
            ("Whole Fresh Milk", "Dairy & Eggs", 1.0, "L", "Fridge", (today - timedelta(days=5)).isoformat(), (today + timedelta(days=2)).isoformat(), "Opened bottle, use soon"),
            ("Fresh Baby Spinach", "Vegetables", 250.0, "g", "Fridge", (today - timedelta(days=4)).isoformat(), (today + timedelta(days=3)).isoformat(), "Use for salad or smoothie"),
            ("Whole Wheat Bread", "Bakery", 1.0, "loaf", "Pantry", (today - timedelta(days=4)).isoformat(), (today + timedelta(days=1)).isoformat(), "Soft bread, eat within 24h"),
            ("Sweet Strawberries", "Fruits", 1.0, "pack", "Fridge", (today - timedelta(days=3)).isoformat(), (today + timedelta(days=2)).isoformat(), "Check for freshness"),

            # Expired Items (< 0 days)
            ("Sliced Cheddar Cheese", "Dairy & Eggs", 200.0, "g", "Fridge", (today - timedelta(days=14)).isoformat(), (today - timedelta(days=2)).isoformat(), "Past best by date"),
            ("Canned Tomato Sauce", "Canned Goods", 1.0, "can", "Pantry", (today - timedelta(days=60)).isoformat(), (today - timedelta(days=5)).isoformat(), "Expired last week")
        ]

        cursor.executemany("""
            INSERT INTO food_inventory (user_id, name, category, quantity, unit, storage_location, purchase_date, expiry_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [(user_id, *f) for f in sample_foods])

        # Seed sample daily consumption
        sample_consumptions = [
            (user_id, None, "Farm Fresh Eggs", 2.0, "pcs", today.isoformat(), "Breakfast", "Made scrambled eggs"),
            (user_id, None, "Whole Fresh Milk", 250.0, "ml", today.isoformat(), "Breakfast", "With coffee"),
            (user_id, None, "Crisp Fuji Apples", 1.0, "pcs", today.isoformat(), "Snacks", "Afternoon healthy snack")
        ]
        cursor.executemany("""
            INSERT INTO daily_consumption (user_id, food_id, food_name, quantity_consumed, unit, date_consumed, meal_type, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_consumptions)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    print("Initializing FoodNest database...")
    init_db()
    seed_data()
    print("FoodNest database ready!")
