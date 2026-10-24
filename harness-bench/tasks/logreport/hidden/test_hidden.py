import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
EXPECTED = 'requests: 4940\ntop ips:\n  10.0.0.37 474\n  10.0.3.19 453\n  10.0.3.4 428\n  10.0.2.10 425\n  10.0.3.26 405\nserver errors: 7.8%\n'


class Hidden(unittest.TestCase):
    def test_other_log(self):
        p = subprocess.run([sys.executable, os.path.join(HERE, "report.py"), os.path.join(HERE, "other.log")],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(p.stdout, EXPECTED, p.stderr[-500:])


if __name__ == "__main__":
    unittest.main()
