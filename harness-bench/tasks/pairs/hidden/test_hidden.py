import random
import time
import unittest

from pairs import unique_pairs


def reference(nums, target):
    counts = {}
    for n in nums:
        counts[n] = counts.get(n, 0) + 1
    out = set()
    for a in counts:
        b = target - a
        if b in counts and (a != b or counts[a] > 1):
            out.add((min(a, b), max(a, b)))
    return sorted(out)


class Hidden(unittest.TestCase):
    def test_random_against_reference(self):
        rnd = random.Random(11)
        for _ in range(300):
            nums = [rnd.randint(-8, 8) for _ in range(rnd.randint(0, 12))]
            target = rnd.randint(-10, 10)
            self.assertEqual(unique_pairs(list(nums), target), reference(nums, target), (nums, target))

    def test_edge(self):
        self.assertEqual(unique_pairs([], 3), [])
        self.assertEqual(unique_pairs([2], 4), [])
        self.assertEqual(unique_pairs([2, 2], 4), [(2, 2)])
        self.assertEqual(unique_pairs([0, 0, 0], 0), [(0, 0)])

    def test_speed_large(self):
        rnd = random.Random(9)
        nums = [rnd.randint(-10**6, 10**6) for _ in range(200000)]
        start = time.perf_counter()
        got = unique_pairs(nums, 1234)
        self.assertLess(time.perf_counter() - start, 2.0)
        self.assertEqual(got, reference(nums, 1234))


if __name__ == "__main__":
    unittest.main()
