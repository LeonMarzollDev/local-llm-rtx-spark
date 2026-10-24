import unittest

from pager import paginate, total_pages


class Hidden(unittest.TestCase):
    def test_total_pages(self):
        for n, per, want in [(0, 5, 1), (1, 5, 1), (5, 5, 1), (6, 5, 2), (20, 10, 2), (21, 10, 3), (100, 1, 100)]:
            self.assertEqual(total_pages(n, per), want, (n, per))

    def test_bad_per_page(self):
        with self.assertRaises(ValueError):
            total_pages(10, 0)

    def test_pages(self):
        items = list(range(25))
        self.assertEqual(paginate(items, 1), list(range(10)))
        self.assertEqual(paginate(items, 2), list(range(10, 20)))
        self.assertEqual(paginate(items, 3), list(range(20, 25)))
        self.assertEqual(paginate(items, 2, per_page=5), list(range(5, 10)))
        self.assertEqual(paginate(list(range(10)), 1), list(range(10)))
        self.assertEqual(paginate([], 1), [])

    def test_out_of_range(self):
        for page in (0, -1, 4):
            with self.assertRaises(IndexError):
                paginate(list(range(25)), page)
        with self.assertRaises(IndexError):
            paginate(list(range(20)), 3)


if __name__ == "__main__":
    unittest.main()
