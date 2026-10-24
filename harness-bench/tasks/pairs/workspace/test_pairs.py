import random
import time
import unittest

from pairs import unique_pairs


class PairsTest(unittest.TestCase):
    def test_small(self):
        self.assertEqual(unique_pairs([1, 2, 3, 4, 5], 6), [(1, 5), (2, 4)])
        self.assertEqual(unique_pairs([3, 3, 4], 6), [(3, 3)])
        self.assertEqual(unique_pairs([3, 4], 6), [])

    def test_speed(self):
        rnd = random.Random(5)
        nums = [rnd.randint(-5000, 5000) for _ in range(20000)]
        start = time.perf_counter()
        unique_pairs(nums, 77)
        self.assertLess(time.perf_counter() - start, 2.0)


if __name__ == "__main__":
    unittest.main()
