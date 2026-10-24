import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from shop import pricing  # noqa: E402
from shop.cart import Cart  # noqa: E402
from shop.checkout import receipt  # noqa: E402


class Hidden(unittest.TestCase):
    def test_no_old_name(self):
        for root, _, files in os.walk(HERE):
            for name in files:
                if name.endswith(".py") and name != "test_hidden.py":
                    with open(os.path.join(root, name)) as f:
                        self.assertNotIn("calc_total", f.read(), name)
        self.assertFalse(hasattr(pricing, "calc_total"))

    def test_compute_total(self):
        items = [{"price": 3.5, "qty": 2}, {"price": 9.0, "qty": 1}]
        self.assertEqual(pricing.compute_total(items), 16.0)
        self.assertEqual(pricing.compute_total(items, "WELCOME10"), 14.4)
        self.assertEqual(pricing.compute_total(items, "WELCOME10", tax_rate=0.19), 17.14)
        self.assertEqual(pricing.compute_total(items, tax_rate=0.07), 17.12)
        with self.assertRaises(TypeError):
            pricing.compute_total(items, None, 0.19)   # keyword-only

    def test_cart_and_receipt(self):
        cart = Cart()
        cart.add("tea", 3.5, 2)
        cart.add("cup", 9.0)
        cart.apply_code("WELCOME10")
        self.assertEqual(receipt(cart), "2 x tea: 7.00 EUR\n1 x cup: 9.00 EUR\ntotal: 14.40 EUR")
        cart.tax_rate = 0.19
        self.assertEqual(cart.total(), 17.14)
        self.assertEqual(receipt(cart), "2 x tea: 7.00 EUR\n1 x cup: 9.00 EUR\nnet: 14.40 EUR\ntax 19%: 2.74 EUR\n"
                                        "total: 17.14 EUR")

    def test_agent_tests_pass(self):
        p = subprocess.run([sys.executable, "-m", "unittest", "test_shop"], cwd=HERE, capture_output=True, text=True,
                           timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr[-500:])


if __name__ == "__main__":
    unittest.main()
