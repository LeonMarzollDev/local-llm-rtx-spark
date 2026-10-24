#!/usr/bin/env python3
"""Single-stream speed test against the running local model (OpenAI-compatible API).

Usage: bench.py <base_url> <label>
Runs the same three prompts every time (code, prose, structured) so variants can be compared,
prints time-to-first-token and decode speed, and appends the results to ~/llm/bench-results.csv.
"""
import csv
import json
import statistics
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

PROMPTS = {
    "code": "Write a Python class implementing an LRU cache with get/put in O(1), with type hints, "
            "docstrings and a short usage example.",
    "prose": "Explain to a non-technical reader how a heat pump heats a house in winter, "
             "in about 400 words.",
    "structured": "List 15 European capital cities with country, population and one famous landmark "
                  "each, as a markdown table.",
}
MAX_TOKENS = 512


def model_id(base):
    with urllib.request.urlopen(f"{base}/models") as r:
        return json.load(r)["data"][0]["id"]


def run(base, model, prompt):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
        "temperature": 0,
        "stream": True,
        "stream_options": {"include_usage": True},
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(f"{base}/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    start = time.perf_counter()
    first = None
    tokens = 0
    with urllib.request.urlopen(req) as r:
        for raw in r:
            line = raw.decode().strip()
            if not line.startswith("data:") or line == "data: [DONE]":
                continue
            chunk = json.loads(line[5:])
            if first is None and chunk.get("choices") and chunk["choices"][0]["delta"].get("content"):
                first = time.perf_counter()
            if chunk.get("usage"):
                tokens = chunk["usage"]["completion_tokens"]
    end = time.perf_counter()
    first = first or end
    decode = (tokens - 1) / (end - first) if end > first and tokens > 1 else 0.0
    return first - start, decode, tokens


def main():
    base, label = sys.argv[1], sys.argv[2]
    model = model_id(base)
    run(base, model, "Say hi.")  # warm-up
    rows = []
    print(f"{label} ({model}), {MAX_TOKENS} tokens per prompt, temperature 0")
    for name, prompt in PROMPTS.items():
        ttft, tps, n = run(base, model, prompt)
        rows.append((name, ttft, tps, n))
        print(f"  {name:<11} first token {ttft:5.2f}s   {tps:6.1f} tok/s   ({n} tokens)")
    median = statistics.median(r[2] for r in rows)
    print(f"  median decode: {median:.1f} tok/s")

    out = Path.home() / "llm" / "bench-results.csv"
    new = not out.exists()
    with out.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "label", "model", "prompt", "ttft_s", "tok_per_s", "tokens"])
        for name, ttft, tps, n in rows:
            w.writerow([datetime.now().isoformat(timespec="seconds"), label, model, name,
                        f"{ttft:.2f}", f"{tps:.1f}", n])


if __name__ == "__main__":
    main()
