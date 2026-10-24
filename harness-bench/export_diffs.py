#!/usr/bin/env python3
"""Blind code review material: the change each harness made, as a unified diff against the task's original
workspace, under a random id. The id -> harness key goes to a separate file the reviewer does not get.

    export_diffs.py LABEL OUTDIR
"""
import json
import os
import random
import subprocess
import sys

BENCH = os.path.dirname(os.path.abspath(__file__))
label, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
runs = [json.loads(line) for line in open(f"{BENCH}/results.jsonl")]
runs = [r for r in runs if r["label"] == label]
rnd = random.Random()
ids = rnd.sample(range(100, 1000), len(runs))
key = {}
for r, i in zip(runs, ids):
    name = f"{r['task']}-{i}"
    key[name] = {"harness": r["harness"], "rep": r["rep"], "passed": r["passed"]}
    workspace = f"{BENCH}/runs/{label}/{r['harness']}/{r['task']}-{r['rep']}/workspace"
    diff = subprocess.run(["diff", "-ruN", "-x", "__pycache__", "-x", "*.pyc", "-x", "todos.json", "-x", ".*",
                           f"{BENCH}/tasks/{r['task']}/workspace", workspace], capture_output=True, text=True).stdout
    diff = diff.replace(f"{BENCH}/tasks/{r['task']}/workspace", "a").replace(workspace, "b")
    with open(f"{out}/{name}.diff", "w") as f:
        f.write(diff)
with open(f"{BENCH}/review-key-{label}.json", "w") as f:
    json.dump(key, f, indent=1, sort_keys=True)
print(f"{len(runs)} diffs in {out}, key in review-key-{label}.json")
