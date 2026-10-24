#!/usr/bin/env python3
"""Time to first token for long prompts: new each time (no cache) and the same one again (prefix cache).

    prefill.py LABEL
"""
import json
import sys
import time
import urllib.request
import uuid

URL = "http://127.0.0.1:8000/v1/chat/completions"
FILLER = ("The committee reviewed the quarterly logistics report, noting delays at two warehouses, "
          "a rise in fuel costs and a new routing system that shortened average delivery times. ")


def first_token(prompt):
    body = {"model": "local", "messages": [{"role": "user", "content": prompt}], "max_tokens": 1,
            "temperature": 0, "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=600) as r:
        tokens = json.load(r)["usage"]["prompt_tokens"]
    return time.perf_counter() - t0, tokens


for repeats in (60, 250, 1000):              # about 2k, 8k, 32k tokens
    prompt = f"[{uuid.uuid4()}] " + FILLER * repeats + "\nSummarize the report in one sentence."
    fresh, tokens = first_token(prompt)
    cached, _ = first_token(prompt)
    print(f"{sys.argv[1]}: {tokens:6d} prompt tokens  new {fresh:6.2f} s ({tokens / fresh:5.0f} tok/s)  "
          f"again {cached:5.2f} s")
