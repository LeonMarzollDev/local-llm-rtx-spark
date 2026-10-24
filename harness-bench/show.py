"""Results of a label as a table: show.py LABEL [--follow]"""
import json
import sys
import time

label = sys.argv[1]


def fmt(r):
    flags = (" TIMEOUT" if r["timed_out"] else "") + (" tests-changed" if r["tests_changed"] else "")
    return (f"{r['harness']:9s} {r['task']:10s} rep{r['rep']} {'PASS' if r['passed'] else 'FAIL'} {r['seconds']:4d}s "
            f"{r['requests']:3d} calls {r['prompt']:7d} in {r['generated']:6d} out  {r['hidden_tests'][:50]}{flags}")


with open(sys.argv[0].rsplit("/", 1)[0] + "/results.jsonl") as f:
    while True:
        line = f.readline()
        if not line:
            if "--follow" not in sys.argv:
                break
            time.sleep(2)
            continue
        r = json.loads(line)
        if r["label"] == label:
            print(fmt(r), flush=True)
