import unittest

from shop.cart import Cart
from shop.checkout import receipt


class ShopTest(unittest.TestCase):
    def test_total(self):
        cart = Cart()
        cart.add("tea", 3.5, 2)
        cart.add("cup", 9.0)
        self.assertEqual(cart.total(), 16.0)
        cart.apply_code("WELCOME10")
        self.assertEqual(cart.total(), 14.4)

    def test_receipt(self):
        cart = Cart()
        cart.add("tea", 3.5, 2)
        self.assertEqual(receipt(cart), "2 x tea: 7.00 EUR\ntotal: 7.00 EUR")


if __name__ == "__main__":
    unittest.main()
