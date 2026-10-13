import unittest
import json
from app import app
from database import get_db_connection, init_db

class FoodNestAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_user_registration(self):
        """Verify new user registration flow."""
        res = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'test@freshpantry.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = 'testuser'").fetchone()
        self.assertIsNotNone(user, "Registered user should exist in DB")
        conn.close()

    def test_02_authentication(self):
        """Test sign in with registered user credentials."""
        # Incorrect password
        res = self.client.post('/login', data={'username': 'testuser', 'password': 'wrongpassword'}, follow_redirects=True)
        self.assertIn(b'Invalid username/email or password', res.data)

        # Correct password
        res = self.client.post('/login', data={'username': 'testuser', 'password': 'password123'}, follow_redirects=True)
        self.assertIn(b'Keep Food Fresh', res.data)
        self.assertIn(b'Total Food Items', res.data)

    def test_03_home_dashboard_counters(self):
        """Verify home page loads the 4 metric cards."""
        conn = get_db_connection()
        user = conn.execute("SELECT id FROM users WHERE username = 'testuser'").fetchone()
        conn.close()

        with self.client.session_transaction() as sess:
            sess['user_id'] = user['id']
            sess['username'] = 'testuser'

        res = self.client.get('/home')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Welcome to FreshPantry', res.data)
        self.assertIn(b'Total Food Items', res.data)
        self.assertIn(b'Fresh Items', res.data)
        self.assertIn(b'Expiring Soon', res.data)
        self.assertIn(b'Expired Items', res.data)
        self.assertIn(b'freshpantry2026@gmail.com', res.data)

    def test_04_inventory_crud(self):
        """Test adding, editing, and deleting inventory items."""
        conn = get_db_connection()
        user = conn.execute("SELECT id FROM users WHERE username = 'testuser'").fetchone()
        conn.close()

        with self.client.session_transaction() as sess:
            sess['user_id'] = user['id']
            sess['username'] = 'testuser'

        # Add item
        res = self.client.post('/api/inventory/add', data={
            'name': 'Test Avocado Pack',
            'category': 'Fruits',
            'quantity': 4,
            'unit': 'pcs',
            'storage_location': 'Fridge',
            'purchase_date': '2026-10-13',
            'expiry_date': '2026-10-25',
            'notes': 'Ripe avocados'
        })
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        item_id = data['item_id']

        # Edit item
        res_edit = self.client.post(f'/api/inventory/edit/{item_id}', data={
            'name': 'Test Avocado Pack (Updated)',
            'category': 'Fruits',
            'quantity': 3,
            'unit': 'pcs',
            'storage_location': 'Fridge',
            'purchase_date': '2026-10-13',
            'expiry_date': '2026-10-28',
            'notes': 'Updated note'
        })
        self.assertTrue(json.loads(res_edit.data)['success'])

        # Delete item
        res_del = self.client.post(f'/api/inventory/delete/{item_id}')
        self.assertTrue(json.loads(res_del.data)['success'])

    def test_05_daily_food_consumption(self):
        """Test consuming an inventory item and daily usage logging."""
        conn = get_db_connection()
        user = conn.execute("SELECT id FROM users WHERE username = 'testuser'").fetchone()

        # Insert a food item to consume
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO food_inventory (user_id, name, category, quantity, unit, storage_location, purchase_date, expiry_date, notes)
            VALUES (?, 'Organic Apples', 'Fruits', 6.0, 'pcs', 'Fridge', '2026-10-13', '2026-10-20', 'Fresh apples')
        """, (user['id'],))
        conn.commit()
        item_id = cursor.lastrowid
        conn.close()

        with self.client.session_transaction() as sess:
            sess['user_id'] = user['id']
            sess['username'] = 'testuser'

        # Consume 2 apples
        res = self.client.post(f'/api/inventory/consume/{item_id}', data={
            'quantity': 2,
            'meal_type': 'Breakfast',
            'date': '2026-10-13',
            'notes': 'Morning snack'
        })
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['remaining_quantity'], 4.0)

        # Check daily usage page
        res_usage = self.client.get('/daily-usage?date=2026-10-13')
        self.assertEqual(res_usage.status_code, 200)
        self.assertIn(b'Organic Apples', res_usage.data)

    def test_06_nav_routes(self):
        """Verify About, Contact, and Profile pages."""
        conn = get_db_connection()
        user = conn.execute("SELECT id FROM users WHERE username = 'testuser'").fetchone()
        conn.close()

        with self.client.session_transaction() as sess:
            sess['user_id'] = user['id']
            sess['username'] = 'testuser'

        res_about = self.client.get('/about')
        self.assertEqual(res_about.status_code, 200)
        self.assertIn(b'About FreshPantry', res_about.data)

        res_contact = self.client.get('/contact')
        self.assertEqual(res_contact.status_code, 200)
        self.assertIn(b'freshpantry2026@gmail.com', res_contact.data)

        res_profile = self.client.get('/profile')
        self.assertEqual(res_profile.status_code, 200)
        self.assertIn(b'testuser', res_profile.data)

if __name__ == '__main__':
    unittest.main()
