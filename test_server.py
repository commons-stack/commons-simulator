import unittest
from server import app

class RouteTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = "secret"
        self.app = app.test_client()
    def test_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    def test_abc(self):
        args = {
            "initial_supply": 1114444.3925780114,
            "exit_tribute": 0.2,
            "kappa": 2,
            "hatch_price": 0.1,
            "hatch_tribute": 0.25
        }
        response = self.app.post('/abc', data=args, follow_redirects=True)
        self.assertEqual(response.status_code, 200)