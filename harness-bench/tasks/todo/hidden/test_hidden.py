import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def run(*args, env_file):
    env = dict(os.environ, TODO_FILE=env_file)
    p = subprocess.run([sys.executable, os.path.join(HERE, "todo.py"), *args], capture_output=True, text=True, env=env,
                       timeout=30)
    return p.returncode, p.stdout, p.stderr


class Hidden(unittest.TestCase):
    def setUp(self):
        fd, self.file = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.unlink(self.file)

    def test_flow(self):
        f = self.file
        self.assertEqual(run("list", env_file=f)[1], "nothing to do\n")
        self.assertEqual(run("add", "buy milk", env_file=f)[1], "added 1\n")
        self.assertEqual(run("add", "call Anna", env_file=f)[1], "added 2\n")
        self.assertEqual(run("add", "fix bike", env_file=f)[1], "added 3\n")
        self.assertEqual(run("done", "2", env_file=f)[:2], (0, "done 2\n"))
        self.assertEqual(run("list", env_file=f)[1], "1. [ ] buy milk\n2. [x] call Anna\n3. [ ] fix bike\n")
        self.assertEqual(run("list", "--open", env_file=f)[1], "1. [ ] buy milk\n3. [ ] fix bike\n")
        self.assertEqual(run("done", "2", env_file=f)[:2], (0, "done 2\n"))

    def test_unknown_id(self):
        f = self.file
        run("add", "a", env_file=f)
        code, out, err = run("done", "7", env_file=f)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertEqual(err.strip(), "no todo with id 7")

    def test_all_done(self):
        f = self.file
        run("add", "a", env_file=f)
        run("done", "1", env_file=f)
        self.assertEqual(run("list", "--open", env_file=f)[1], "nothing to do\n")
        self.assertEqual(run("list", env_file=f)[1], "1. [x] a\n")


class AgentTests(unittest.TestCase):
    def test_agent_wrote_tests(self):
        path = os.path.join(HERE, "test_todo.py")
        self.assertTrue(os.path.exists(path), "test_todo.py missing")
        p = subprocess.run([sys.executable, "-m", "unittest", "test_todo"], cwd=HERE, capture_output=True, text=True,
                           timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr[-500:])


if __name__ == "__main__":
    unittest.main()
