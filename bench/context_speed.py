"""How generation slows down as the context fills: for each size, a prompt of about N tokens (unrelated test
material, numbered), then 300 tokens of answer, streamed. Measures the wait for the first token (reading the
prompt) and the generation speed after it (tokens/s), separately.

    python3 context_speed.py URL MODEL LABEL N1 N2 ...      e.g. ... local flash-1m 1000 32000 128000
"""
import json
import os
import sys
import time
import urllib.request

url, model, label = sys.argv[1:4]
sizes = [int(n) for n in sys.argv[4:]]
data = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quality-data")
pieces = [r["row"]["question"] for r in json.load(open(f"{data}/gsm8k.json"))["rows"]]
for name in ("humaneval.json", "humaneval2.json"):
    pieces += [r["row"]["prompt"] for r in json.load(open(f"{data}/{name}"))["rows"]]


def prompt(tokens, salt):
    """Unrelated numbered material, ~3.3 characters per token; the salt makes every prompt new (no cache)."""
    parts, n, i = [f"Session {salt}."], 0, 0
    while n < tokens * 3.3:
        parts.append(f"[Item {i}] {pieces[i % len(pieces)]}")
        n += len(parts[-1])
        i += 1
    return "\n\n".join(parts) + "\n\nWrite a detailed, long summary of the material above, item by item."


for size in sizes:
    body = {"model": model, "messages": [{"role": "user", "content": prompt(size, time.time_ns())}],
            "temperature": 0, "max_tokens": 300, "stream": True, "stream_options": {"include_usage": True},
            "chat_template_kwargs": {"enable_thinking": False}, "ignore_eos": True}
    req = urllib.request.Request(url + "/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    start, first, last, used, out = time.time(), None, None, None, 0
    with urllib.request.urlopen(req, timeout=7200) as resp:
        for raw in resp:
            line = raw.decode().strip()
            if not line.startswith("data:") or line.endswith("[DONE]"):
                continue
            chunk = json.loads(line[5:])
            if chunk.get("usage"):
                used, out = chunk["usage"]["prompt_tokens"], chunk["usage"]["completion_tokens"]
            if chunk.get("choices") and chunk["choices"][0]["delta"].get("content"):
                first = first or time.time()
                last = time.time()
    decode = (out - 1) / (last - first) if first and last and last > first and out > 1 else 0
    print(f"{label}: {used:>9,} context tokens   first token after {first - start:7.1f} s   "
          f"generation {decode:5.1f} tok/s ({out} tokens)", flush=True)
