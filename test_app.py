import unittest
import json
from app import app
from database import get_db_connection, init_db, seed_data

class FoodNestAppTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_database_and_seed_data(self):
        """Verify DB tables and initial sample food inventory."""
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = 'demo'").fetchone()
        self.assertIsNotNone(user, "Demo user should exist in DB")

        inv_count = conn.execute("SELECT COUNT(*) as count FROM food_inventory WHERE user_id = ?", (user['id'],)).fetchone()['count']
        self.assertGreaterEqual(inv_count, 10, "Should have seeded food inventory items")
        conn.close()

    def test_02_authentication(self):
        """Test sign in with demo credentials."""
        # Incorrect password
        res = self.client.post('/login', data={'username': 'demo', 'password': 'wrong'}, follow_redirects=True)
        self.assertIn(b'Invalid username/email or password', res.data)

        # Correct password
        res = self.client.post('/login', data={'username': 'demo', 'password': 'demo123'}, follow_redirects=True)
        self.assertIn(b'Keep Food Fresh', res.data)
        self.assertIn(b'Total Food Items', res.data)

    def test_03_home_dashboard_counters(self):
        """Verify home page loads the 4 metric cards."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'demo'

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
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'demo'

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
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'demo'

        conn = get_db_connection()
        item = conn.execute("SELECT id, quantity FROM food_inventory WHERE user_id = 1 AND name = 'Farm Fresh Eggs'").fetchone()
        conn.close()

        initial_qty = item['quantity']

        # Consume 2 eggs
        res = self.client.post(f'/api/inventory/consume/{item["id"]}', data={
            'quantity': 2,
            'meal_type': 'Breakfast',
            'date': '2026-10-13',
            'notes': 'Boiled eggs'
        })
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['remaining_quantity'], initial_qty - 2)

        # Check daily usage page
        res_usage = self.client.get('/daily-usage?date=2026-10-13')
        self.assertEqual(res_usage.status_code, 200)
        self.assertIn(b'Farm Fresh Eggs', res_usage.data)

    def test_06_nav_routes(self):
        """Verify About, Contact, and Profile pages."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'demo'

        res_about = self.client.get('/about')
        self.assertEqual(res_about.status_code, 200)
        self.assertIn(b'About FreshPantry', res_about.data)

        res_contact = self.client.get('/contact')
        self.assertEqual(res_contact.status_code, 200)
        self.assertIn(b'freshpantry2026@gmail.com', res_contact.data)

        res_profile = self.client.get('/profile')
        self.assertEqual(res_profile.status_code, 200)
        self.assertIn(b'demo', res_profile.data)

if __name__ == '__main__':
    unittest.main()
