"""Quality of a local model for coding and agentic work, on standard tests with checkable answers:
  code     HumanEval, 40 of the 164 tasks: the function the model writes runs against the task's tests, in a
           container without network (read-only, 512 MB, 1 CPU)
  tools    BFCL (Berkeley Function Calling Leaderboard) v3, 20 each of simple / multiple / parallel: the right
           function(s) with the right arguments, through the OpenAI tools API
  math     GSM8K, 50 of the test problems: multi-step reasoning, the final number counts
Temperature 0, thinking off (as Spark and the benchmarks use the models).

    python3 quality.py URL MODEL LABEL              e.g. http://127.0.0.1:8000/v1 local 27b-mtp4
    python3 quality.py --compare LABEL_A LABEL_B   how many answers are identical (speculation is lossless)

Writes quality-results/LABEL.json (every answer) and appends the summary to quality-results/summary.txt.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "quality-data")
RESULTS = os.path.join(HERE, "quality-results")
SANDBOX_IMAGE = "searxng/searxng:2026.10.19-81371861f"     # any local image with python3
N_CODE, N_TOOLS, N_MATH = 40, 20, 50


def chat(url, model, messages, max_tokens, tools=None):
    body = {"model": model, "messages": messages, "temperature": 0, "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": False}}
    if tools:
        body["tools"] = tools
    req = urllib.request.Request(url + "/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.load(resp)["choices"][0]["message"]


def spaced(items, n):
    """n items spread evenly over the whole set (not just the first, often easiest ones)."""
    step = len(items) / n
    return [items[int(i * step)] for i in range(n)]


# ---------------------------------------------------------------- code (HumanEval)
def humaneval():
    rows = []
    for name in ("humaneval.json", "humaneval2.json"):
        rows += [r["row"] for r in json.load(open(os.path.join(DATA, name)))["rows"]]
    return spaced(rows, N_CODE)


def code_from(reply, task):
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", reply, re.S)
    code = max(blocks, key=len) if blocks else reply
    if f"def {task['entry_point']}" not in code:          # only the body came back
        code = task["prompt"] + code
    return code


def run_code(tasks, codes):
    """All programs in one container without network; True where the tests passed."""
    with tempfile.TemporaryDirectory(dir=HERE) as tmp:
        for i, (task, code) in enumerate(zip(tasks, codes)):
            with open(os.path.join(tmp, f"t{i}.py"), "w") as f:
                f.write(code + "\n\n" + task["test"] + f"\n\ncheck({task['entry_point']})\n")
        with open(os.path.join(tmp, "run.py"), "w") as f:
            f.write("import json, subprocess, sys\nout = []\n"
                    f"for i in range({len(tasks)}):\n"
                    "    try:\n"
                    "        r = subprocess.run([sys.executable, f'/w/t{i}.py'], capture_output=True, timeout=10)\n"
                    "        out.append(r.returncode == 0)\n"
                    "    except subprocess.TimeoutExpired:\n"
                    "        out.append(False)\n"
                    "print(json.dumps(out))\n")
        os.chmod(tmp, 0o755)
        for name in os.listdir(tmp):
            os.chmod(os.path.join(tmp, name), 0o644)
        cmd = (f"docker run --rm --network none --memory 512m --cpus 1 --read-only --tmpfs /tmp "
               f"-v {tmp}:/w:ro --entrypoint python3 {SANDBOX_IMAGE} /w/run.py")
        res = subprocess.run(["sg", "docker", "-c", cmd], capture_output=True, text=True, timeout=900)
        return json.loads(res.stdout.strip().splitlines()[-1])


# ---------------------------------------------------------------- tools (BFCL)
TYPES = {"dict": "object", "float": "number", "tuple": "array", "integer": "integer", "string": "string",
         "boolean": "boolean", "array": "array", "number": "number", "object": "object"}


def schema(s):
    """BFCL's parameter schema (Python-ish types) as JSON schema."""
    if isinstance(s, dict):
        out = {}
        for k, v in s.items():
            if k == "type":
                if v in TYPES:
                    out["type"] = TYPES[v]
            elif k in ("properties",):
                out[k] = {name: schema(p) for name, p in v.items()}
            elif k in ("items", "additionalProperties"):
                out[k] = schema(v)
            elif k not in ("optional", "format"):
                out[k] = v
        return out
    return s


def bfcl():
    tasks = []
    for kind in ("simple", "multiple", "parallel"):
        questions = [json.loads(l) for l in open(os.path.join(DATA, f"BFCL_v3_{kind}.json"))]
        answers = {a["id"]: a["ground_truth"] for a in
                   (json.loads(l) for l in open(os.path.join(DATA, f"possible_answer_BFCL_v3_{kind}.json")))}
        for q in spaced(questions, N_TOOLS):
            tools = [{"type": "function", "function": {"name": f["name"].replace(".", "_"),
                                                       "description": f.get("description", ""),
                                                       "parameters": schema(f["parameters"])}}
                     for f in q["function"]]
            tasks.append({"id": q["id"], "kind": kind, "messages": q["question"][0], "tools": tools,
                          "truth": answers[q["id"]]})
    return tasks


def norm(v):
    if isinstance(v, str):
        return re.sub(r"[\s,./\-_*^]", "", v.lower())
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, (list, tuple)):
        return [norm(x) for x in v]
    if isinstance(v, dict):
        return {k: norm(x) for k, x in v.items()}
    return v


def call_fits(call, expected):
    """One call against one expected {function: {param: [acceptable values]}} (BFCL's rule: every given
    parameter has an acceptable value; one left out is fine only if "" is acceptable)."""
    (fname, params), = expected.items()
    if call["name"] != fname.replace(".", "_"):
        return False
    args = call["args"]
    for p, ok in params.items():
        if p in args:
            if norm(args[p]) not in [norm(x) for x in ok if x != ""]:
                return False
        elif "" not in ok:
            return False
    return all(p in params for p in args)


def tools_right(calls, truth):
    if len(calls) != len(truth):
        return False
    left = list(calls)
    for expected in truth:                            # any order (parallel calls)
        hit = next((c for c in left if call_fits(c, expected)), None)
        if hit is None:
            return False
        left.remove(hit)
    return True


# ---------------------------------------------------------------- math (GSM8K)
def gsm8k():
    return spaced([r["row"] for r in json.load(open(os.path.join(DATA, "gsm8k.json")))["rows"]], N_MATH)


def number(text):
    m = re.search(r"ANSWER:\s*\$?(-?[\d,]*\.?\d+)", text)
    found = m.group(1) if m else (re.findall(r"-?[\d,]*\.?\d+", text) or [""])[-1]
    try:
        return float(found.replace(",", ""))
    except ValueError:
        return None


# ---------------------------------------------------------------- run
def run(url, model, label):
    os.makedirs(RESULTS, exist_ok=True)
    out, summary = {"label": label, "model": model}, {}
    start = time.time()
    tasks = humaneval()
    replies = [chat(url, model, [{"role": "user", "content":
                                  "Complete this Python function. Reply with the whole function in one ```python "
                                  "code block and nothing else.\n\n" + t["prompt"]}], 1024)["content"] or ""
               for t in tasks]
    passed = run_code(tasks, [code_from(r, t) for r, t in zip(replies, tasks)])
    out["code"] = [{"id": t["task_id"], "reply": r, "ok": ok} for t, r, ok in zip(tasks, replies, passed)]
    summary["code"] = (sum(passed), len(tasks), time.time() - start)

    start = time.time()
    results = []
    for t in bfcl():
        msg = chat(url, model, t["messages"], 512, t["tools"])
        calls = []
        for c in msg.get("tool_calls") or []:
            try:
                args = json.loads(c["function"]["arguments"] or "{}")
            except ValueError:
                args = {"_unparsable": c["function"]["arguments"]}
            calls.append({"name": c["function"]["name"], "args": args})
        results.append({"id": t["id"], "kind": t["kind"], "calls": calls, "text": msg.get("content") or "",
                        "ok": tools_right(calls, t["truth"])})
    out["tools"] = results
    for kind in ("simple", "multiple", "parallel"):
        part = [r for r in results if r["kind"] == kind]
        summary[f"tools-{kind}"] = (sum(r["ok"] for r in part), len(part), None)
    summary["tools"] = (sum(r["ok"] for r in results), len(results), time.time() - start)

    start = time.time()
    results = []
    for p in gsm8k():
        reply = chat(url, model, [{"role": "user", "content": p["question"] + "\n\nSolve it step by step, briefly. "
                                   "Give the final number on the last line as: ANSWER: <number>"}], 768)["content"] or ""
        gold = float(p["answer"].split("####")[-1].strip().replace(",", ""))
        got = number(reply)
        results.append({"q": p["question"][:80], "reply": reply, "ok": got is not None and abs(got - gold) < 1e-6})
    out["math"] = results
    summary["math"] = (sum(r["ok"] for r in results), len(results), time.time() - start)

    json.dump(out, open(os.path.join(RESULTS, f"{label}.json"), "w"), indent=1, ensure_ascii=False)
    lines = [f"{label} ({time.strftime('%Y-%m-%d %H:%M')}):"]
    for key, (ok, n, secs) in summary.items():
        lines.append(f"  {key:15s} {ok:3d}/{n:<3d} {100 * ok / n:5.1f} %" + (f"   ({secs / 60:.1f} min)" if secs else ""))
    text = "\n".join(lines)
    print(text)
    with open(os.path.join(RESULTS, "summary.txt"), "a") as f:
        f.write(text + "\n")


def compare(a, b):
    A, B = (json.load(open(os.path.join(RESULTS, f"{x}.json"))) for x in (a, b))
    for key, field in (("code", "reply"), ("tools", "calls"), ("math", "reply")):
        same = sum(x[field] == y[field] for x, y in zip(A[key], B[key]))
        ok_same = sum(x["ok"] == y["ok"] for x, y in zip(A[key], B[key]))
        print(f"  {key:6s} identical answers {same}/{len(A[key])}, same verdict {ok_same}/{len(A[key])}")


if __name__ == "__main__":
    if sys.argv[1] == "--compare":
        compare(sys.argv[2], sys.argv[3])
    else:
        run(*sys.argv[1:4])
