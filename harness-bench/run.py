#!/usr/bin/env python3
"""Which coding harness gets the most out of the local model? Each harness gets the same task in a fresh copy of
the task's workspace, in a bubblewrap sandbox (system read-only; writable: the run folder with the workspace and a
fresh home for the harness, so the real ~/.qwen, ~/.config/opencode and ~/.claude stay untouched). Afterwards the
task's hidden tests decide. Tokens and model calls come from vLLM's /metrics.

    run.py [--harness qwen,opencode,claude] [--tasks pager,todo,...] [--reps 1] [--label NAME]
Results: results.jsonl (one line per run), the run folders under runs/.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request

BENCH = os.path.dirname(os.path.abspath(__file__))
TASKS = ["pager", "todo", "shop", "logreport", "pairs"]
HARNESSES = ["qwen", "opencode", "claude"]
API = "http://127.0.0.1:8000"
TIMEOUT = 15 * 60
PROTECTED = {"pager": ["test_pager.py"], "pairs": ["test_pairs.py"]}   # "do not change the tests"
SUFFIX = "\n\nWork only in the current directory. When the task is done, stop."

OPENCODE_CONFIG = {
    "$schema": "https://opencode.ai/config.json",
    "provider": {"local": {
        "npm": "@ai-sdk/openai-compatible", "name": "Local vLLM",
        "options": {"baseURL": f"{API}/v1", "apiKey": "local"},
        "models": {"local": {"name": "Local model", "limit": {"context": 262144, "output": 32768}}}}},
    "model": "local/local",
    "autoupdate": False,
}
CLAUDE_ENV = {
    "ANTHROPIC_BASE_URL": API, "ANTHROPIC_AUTH_TOKEN": "local", "ANTHROPIC_MODEL": "local",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "local", "ANTHROPIC_DEFAULT_SONNET_MODEL": "local",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "local", "CLAUDE_CODE_SUBAGENT_MODEL": "local",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "DISABLE_AUTOUPDATER": "1", "DISABLE_TELEMETRY": "1",
    "DISABLE_ERROR_REPORTING": "1",
}


def metrics():
    """Counters of the model server: prompt tokens, generated tokens, finished requests, prefix cache hits."""
    text = urllib.request.urlopen(f"{API}/metrics", timeout=10).read().decode()
    out = {}
    for key, name in (("prompt", "vllm:prompt_tokens_total"), ("generated", "vllm:generation_tokens_total"),
                      ("requests", "vllm:request_success_total"), ("cache_hits", "vllm:prefix_cache_hits_total")):
        out[key] = sum(float(v) for v in re.findall(rf"^{re.escape(name)}(?:{{[^}}]*}})? ([0-9.e+]+)$", text, re.M))
    return out


def make_home(harness, home):
    os.makedirs(home)
    if harness == "qwen":
        os.makedirs(f"{home}/.qwen/updates")             # the user's auto-updated Qwen Code, mounted read-only
        shutil.copy(os.path.expanduser("~/.qwen/settings.json"), f"{home}/.qwen/settings.json")
    elif harness == "opencode":
        os.makedirs(f"{home}/.config/opencode")
        with open(f"{home}/.config/opencode/opencode.json", "w") as f:
            json.dump(OPENCODE_CONFIG, f, indent=1)


def command(harness, prompt):
    if harness == "qwen":
        return ["qwen", "--yolo", "-o", "json", prompt]
    if harness == "opencode":
        return ["opencode", "run", "--standalone", "--auto", "-m", "local/local", "--format", "json", prompt]
    # --effort xhigh: Claude Code's default "high" is not one of the model's levels (xhigh/medium/low; the others
    # use xhigh as well)
    return ["claude", "-p", prompt, "--dangerously-skip-permissions", "--output-format", "json", "--model", "local",
            "--effort", "xhigh"]


def sandboxed(cmd, run_dir, workspace, home, env):
    args = ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp",
            "--bind", run_dir, run_dir, "--chdir", workspace, "--die-with-parent", "--unshare-pid"]
    if os.path.isdir(f"{home}/.qwen/updates"):
        args += ["--ro-bind", os.path.expanduser("~/.qwen/updates"), f"{home}/.qwen/updates"]
    for key, value in env.items():
        args += ["--setenv", key, value]
    return args + ["--setenv", "HOME", home, "--"] + cmd


def digest(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def check(task, workspace, run_dir):
    """Hidden tests on a copy of the finished workspace."""
    target = f"{run_dir}/check"
    shutil.copytree(workspace, target)
    for name in os.listdir(f"{BENCH}/tasks/{task}/hidden"):
        shutil.copy(f"{BENCH}/tasks/{task}/hidden/{name}", target)
    try:
        p = subprocess.run([sys.executable, "-m", "unittest", "test_hidden"], cwd=target, capture_output=True,
                           text=True, timeout=300)
        tail = p.stderr.strip().splitlines()[-1] if p.stderr.strip() else ""
        return p.returncode == 0, tail, p.stderr[-3000:]
    except subprocess.TimeoutExpired:
        return False, "hidden tests timed out", ""


def run_one(harness, task, rep, label):
    run_dir = f"{BENCH}/runs/{label}/{harness}/{task}-{rep}"
    shutil.rmtree(run_dir, ignore_errors=True)
    os.makedirs(run_dir)
    workspace, home = f"{run_dir}/workspace", f"{run_dir}/home"
    shutil.copytree(f"{BENCH}/tasks/{task}/workspace", workspace)
    make_home(harness, home)
    protected = {name: digest(f"{workspace}/{name}") for name in PROTECTED.get(task, [])}
    prompt = open(f"{BENCH}/tasks/{task}/prompt.txt").read().strip() + SUFFIX
    env = {"VLLM_API_KEY": "local", "PATH": os.environ["PATH"]}
    if harness == "claude":
        env.update(CLAUDE_ENV)
    before, start, timed_out = metrics(), time.time(), False
    with open(f"{run_dir}/output.txt", "w") as out:
        try:
            p = subprocess.run(sandboxed(command(harness, prompt), run_dir, workspace, home, env), stdout=out,
                               stderr=subprocess.STDOUT, timeout=TIMEOUT, stdin=subprocess.DEVNULL)
            code = p.returncode
        except subprocess.TimeoutExpired:
            code, timed_out = None, True
    seconds = time.time() - start
    after = metrics()
    passed, summary, details = check(task, workspace, run_dir)
    changed = [name for name, h in protected.items()
               if not os.path.exists(f"{workspace}/{name}") or digest(f"{workspace}/{name}") != h]
    result = {"label": label, "harness": harness, "task": task, "rep": rep, "passed": passed and not changed,
              "hidden_tests": summary or "OK", "tests_changed": changed, "seconds": round(seconds),
              "exit": code, "timed_out": timed_out,
              **{k: int(after[k] - before[k]) for k in after}}
    with open(f"{run_dir}/check.txt", "w") as f:
        f.write(details)
    with open(f"{BENCH}/results.jsonl", "a") as f:
        f.write(json.dumps(result) + "\n")
    print(json.dumps(result), flush=True)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", default=",".join(HARNESSES))
    ap.add_argument("--tasks", default=",".join(TASKS))
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--label", default=time.strftime("%Y%m%d-%H%M"))
    args = ap.parse_args()
    for rep in range(1, args.reps + 1):
        for task in args.tasks.split(","):
            for harness in args.harness.split(","):        # interleaved: same model state for all three
                run_one(harness, task, rep, args.label)


if __name__ == "__main__":
    main()
