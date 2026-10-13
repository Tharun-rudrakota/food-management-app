import os
import sqlite3
from datetime import datetime, date, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db, seed_data, get_item_status

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
app.secret_key = os.environ.get('SECRET_KEY', 'freshpantry-secret-key-2026-secure')

# Ensure DB is created on startup
with app.app_context():
    init_db()
    seed_data()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

@app.context_processor
def inject_user():
    return {'current_user': get_current_user()}

def get_user_inventory_stats(user_id):
    """Calculates total, fresh, expiring soon, and expired counts for a user."""
    conn = get_db_connection()
    rows = conn.execute("SELECT expiry_date FROM food_inventory WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()

    today = date.today()
    total = len(rows)
    fresh = 0
    expiring_soon = 0
    expired = 0

    for r in rows:
        st = get_item_status(r['expiry_date'], today)
        if st == 'Fresh':
            fresh += 1
        elif st == 'Expiring Soon':
            expiring_soon += 1
        elif st == 'Expired':
            expired += 1

    return {
        'total': total,
        'fresh': fresh,
        'expiring_soon': expiring_soon,
        'expired': expired
    }

# ----------------- AUTHENTICATION ----------------- #

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username_or_email or not password:
            flash('Please provide both username/email and password.', 'danger')
            return render_template('login.html')

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (username_or_email, username_or_email)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Welcome back to FreshPantry, {user["username"]}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')

        conn = get_db_connection()
        existing = conn.execute(
            "SELECT username, email FROM users WHERE username = ? OR email = ?",
            (username, email)
        ).fetchone()

        if existing:
            conn.close()
            if existing['username'].lower() == username.lower():
                flash('Username is already taken.', 'danger')
            else:
                flash('Email is already registered.', 'danger')
            return render_template('register.html')

        hashed_pw = generate_password_hash(password)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        """, (username, email, hashed_pw))
        new_user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        session['user_id'] = new_user_id
        session['username'] = username
        flash('Registration successful! Welcome to FreshPantry.', 'success')
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('login'))

# ----------------- MAIN PAGES ----------------- #

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    user = get_current_user()
    stats = get_user_inventory_stats(user['id'])
    return render_template('home.html', stats=stats)

@app.route('/inventory')
@login_required
def inventory():
    user = get_current_user()
    search_q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    location_filter = request.args.get('location', '').strip()
    category_filter = request.args.get('category', '').strip()

    conn = get_db_connection()
    query = "SELECT * FROM food_inventory WHERE user_id = ?"
    params = [user['id']]

    if search_q:
        query += " AND (name LIKE ? OR notes LIKE ?)"
        params.extend([f"%{search_q}%", f"%{search_q}%"])

    if location_filter:
        query += " AND storage_location = ?"
        params.append(location_filter)

    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    query += " ORDER BY expiry_date ASC"
    items_raw = conn.execute(query, params).fetchall()

    today = date.today()
    items = []
    for r in items_raw:
        item_dict = dict(r)
        st = get_item_status(item_dict['expiry_date'], today)
        item_dict['status'] = st

        try:
            exp_d = datetime.strptime(item_dict['expiry_date'], '%Y-%m-%d').date()
            diff = (exp_d - today).days
            if diff < 0:
                item_dict['days_left_text'] = f"Expired {abs(diff)} day{'s' if abs(diff) != 1 else ''} ago"
            elif diff == 0:
                item_dict['days_left_text'] = "Expires Today!"
            elif diff == 1:
                item_dict['days_left_text'] = "Expires Tomorrow!"
            else:
                item_dict['days_left_text'] = f"{diff} days left"
        except Exception:
            item_dict['days_left_text'] = "-"

        # Apply status filter in python
        if status_filter:
            if item_dict['status'] == status_filter:
                items.append(item_dict)
        else:
            items.append(item_dict)

    # Categories list
    cats = conn.execute("SELECT DISTINCT category FROM food_inventory WHERE user_id = ? ORDER BY category ASC", (user['id'],)).fetchall()
    categories = [c['category'] for c in cats]
    conn.close()

    stats = get_user_inventory_stats(user['id'])

    return render_template(
        'inventory.html',
        items=items,
        stats=stats,
        search_q=search_q,
        status_filter=status_filter,
        location_filter=location_filter,
        category_filter=category_filter,
        categories=categories,
        today_str=today.isoformat()
    )

@app.route('/daily-usage')
@login_required
def daily_usage():
    user = get_current_user()
    today = date.today()
    selected_date = request.args.get('date', today.isoformat())

    conn = get_db_connection()

    # Consumed items for selected date
    consumptions = conn.execute("""
        SELECT * FROM daily_consumption
        WHERE user_id = ? AND date_consumed = ?
        ORDER BY id DESC
    """, (user['id'], selected_date)).fetchall()

    # Expiring soon items ("Cook / Eat First" recommendation list)
    inv_items = conn.execute("""
        SELECT * FROM food_inventory
        WHERE user_id = ?
        ORDER BY expiry_date ASC
    """, (user['id'],)).fetchall()

    urgent_items = []
    for item in inv_items:
        i_dict = dict(item)
        st = get_item_status(i_dict['expiry_date'], today)
        if st in ('Expiring Soon', 'Expired'):
            try:
                exp_d = datetime.strptime(i_dict['expiry_date'], '%Y-%m-%d').date()
                diff = (exp_d - today).days
                i_dict['status'] = st
                i_dict['days_diff'] = diff
                urgent_items.append(i_dict)
            except Exception:
                pass

    urgent_items.sort(key=lambda x: x['days_diff'])

    conn.close()

    return render_template(
        'daily_usage.html',
        consumptions=consumptions,
        urgent_items=urgent_items,
        selected_date=selected_date,
        today_str=today.isoformat()
    )

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        flash('Thank you for reaching out! We have received your message.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()
    stats = get_user_inventory_stats(user['id'])

    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if new_password:
            if new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('profile'))
            if len(new_password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return redirect(url_for('profile'))

            conn = get_db_connection()
            hashed_pw = generate_password_hash(new_password)
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed_pw, user['id']))
            conn.commit()
            conn.close()
            flash('Password updated successfully!', 'success')
        else:
            flash('Profile details saved.', 'info')

        return redirect(url_for('profile'))

    return render_template('profile.html', user=user, stats=stats)

# ----------------- REST API / AJAX ENDPOINTS ----------------- #

@app.route('/api/inventory/add', methods=['POST'])
@login_required
def api_add_inventory():
    user = get_current_user()
    data = request.form or request.get_json()

    name = data.get('name', '').strip()
    category = data.get('category', 'Other').strip()
    quantity = float(data.get('quantity', 1.0))
    unit = data.get('unit', 'pcs').strip()
    storage_location = data.get('storage_location', 'Fridge').strip()
    purchase_date = data.get('purchase_date', date.today().isoformat()).strip()
    expiry_date = data.get('expiry_date', '').strip()
    notes = data.get('notes', '').strip()

    if not name or not expiry_date:
        return jsonify({'success': False, 'message': 'Food name and expiry date are required.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO food_inventory (user_id, name, category, quantity, unit, storage_location, purchase_date, expiry_date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user['id'], name, category, quantity, unit, storage_location, purchase_date, expiry_date, notes))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': f'"{name}" added to inventory!', 'item_id': new_id})

@app.route('/api/inventory/edit/<int:item_id>', methods=['POST'])
@login_required
def api_edit_inventory(item_id):
    user = get_current_user()
    data = request.form or request.get_json()

    conn = get_db_connection()
    item = conn.execute("SELECT * FROM food_inventory WHERE id = ? AND user_id = ?", (item_id, user['id'])).fetchone()
    if not item:
        conn.close()
        return jsonify({'success': False, 'message': 'Item not found.'}), 404

    name = data.get('name', item['name']).strip()
    category = data.get('category', item['category']).strip()
    quantity = float(data.get('quantity', item['quantity']))
    unit = data.get('unit', item['unit']).strip()
    storage_location = data.get('storage_location', item['storage_location']).strip()
    purchase_date = data.get('purchase_date', item['purchase_date']).strip()
    expiry_date = data.get('expiry_date', item['expiry_date']).strip()
    notes = data.get('notes', item['notes']).strip()

    conn.execute("""
        UPDATE food_inventory
        SET name = ?, category = ?, quantity = ?, unit = ?, storage_location = ?, purchase_date = ?, expiry_date = ?, notes = ?
        WHERE id = ? AND user_id = ?
    """, (name, category, quantity, unit, storage_location, purchase_date, expiry_date, notes, item_id, user['id']))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': f'"{name}" updated successfully!'})

@app.route('/api/inventory/delete/<int:item_id>', methods=['POST'])
@login_required
def api_delete_inventory(item_id):
    user = get_current_user()
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM food_inventory WHERE id = ? AND user_id = ?", (item_id, user['id'])).fetchone()
    if not item:
        conn.close()
        return jsonify({'success': False, 'message': 'Item not found.'}), 404

    conn.execute("DELETE FROM food_inventory WHERE id = ? AND user_id = ?", (item_id, user['id']))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': f'"{item["name"]}" deleted from inventory.'})

@app.route('/api/inventory/consume/<int:item_id>', methods=['POST'])
@login_required
def api_consume_inventory(item_id):
    """Consumes some or all of an inventory item and records a daily consumption entry."""
    user = get_current_user()
    data = request.form or request.get_json()

    consume_qty = float(data.get('quantity', 1.0))
    meal_type = data.get('meal_type', 'Lunch')
    consume_date = data.get('date', date.today().isoformat())
    notes = data.get('notes', '')

    conn = get_db_connection()
    item = conn.execute("SELECT * FROM food_inventory WHERE id = ? AND user_id = ?", (item_id, user['id'])).fetchone()
    if not item:
        conn.close()
        return jsonify({'success': False, 'message': 'Item not found.'}), 404

    if consume_qty <= 0:
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid quantity.'}), 400

    # Record consumption
    actual_consumed = min(consume_qty, item['quantity'])
    conn.execute("""
        INSERT INTO daily_consumption (user_id, food_id, food_name, quantity_consumed, unit, date_consumed, meal_type, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user['id'], item['id'], item['name'], actual_consumed, item['unit'], consume_date, meal_type, notes))

    # Deduct quantity from inventory
    remaining_qty = item['quantity'] - actual_consumed
    if remaining_qty <= 0:
        # Fully consumed, remove from inventory
        conn.execute("DELETE FROM food_inventory WHERE id = ?", (item['id'],))
        status_msg = f'Fully consumed "{item["name"]}"! Recorded in daily usage and removed from inventory.'
    else:
        conn.execute("UPDATE food_inventory SET quantity = ? WHERE id = ?", (remaining_qty, item['id']))
        status_msg = f'Consumed {actual_consumed} {item["unit"]} of "{item["name"]}". {remaining_qty} {item["unit"]} remaining in inventory.'

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': status_msg, 'remaining_quantity': remaining_qty})

@app.route('/api/consumption/log', methods=['POST'])
@login_required
def api_log_consumption():
    user = get_current_user()
    data = request.form or request.get_json()

    food_name = data.get('food_name', '').strip()
    quantity = float(data.get('quantity', 1.0))
    unit = data.get('unit', 'pcs').strip()
    consume_date = data.get('date', date.today().isoformat())
    meal_type = data.get('meal_type', 'Lunch')
    notes = data.get('notes', '')

    if not food_name or quantity <= 0:
        return jsonify({'success': False, 'message': 'Food name and quantity required.'}), 400

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO daily_consumption (user_id, food_id, food_name, quantity_consumed, unit, date_consumed, meal_type, notes)
        VALUES (?, NULL, ?, ?, ?, ?, ?, ?)
    """, (user['id'], food_name, quantity, unit, consume_date, meal_type, notes))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': f'Logged {quantity} {unit} of {food_name} for {consume_date}.'})

@app.route('/api/consumption/delete/<int:log_id>', methods=['POST'])
@login_required
def api_delete_consumption(log_id):
    user = get_current_user()
    conn = get_db_connection()
    conn.execute("DELETE FROM daily_consumption WHERE id = ? AND user_id = ?", (log_id, user['id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Consumption entry deleted.'})

if __name__ == '__main__':
    print("Starting FreshPantry Application...")
    print("Dashboard available at: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
