import unittest

from pager import paginate, total_pages


class PagerTest(unittest.TestCase):
    def test_first_page(self):
        self.assertEqual(paginate(list(range(25)), 1), list(range(10)))

    def test_last_partial_page(self):
        self.assertEqual(paginate(list(range(25)), 3), [20, 21, 22, 23, 24])

    def test_exact_multiple(self):
        self.assertEqual(total_pages(20, 10), 2)

    def test_empty(self):
        self.assertEqual(total_pages(0, 10), 1)
        self.assertEqual(paginate([], 1), [])


if __name__ == "__main__":
    unittest.main()
