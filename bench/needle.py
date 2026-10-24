"""Long-context check: one fact hidden halfway in a long text of unrelated material (test problems and code tasks,
numbered), then a question about it. Prints the prompt size, how long reading took and whether the answer is right.
    python3 needle.py URL MODEL TOKENS"""
import json, os, sys, time, urllib.request
url, model, want = sys.argv[1], sys.argv[2], int(sys.argv[3])
data = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quality-data")
pieces = [r["row"]["question"] for r in json.load(open(f"{data}/gsm8k.json"))["rows"]]
for name in ("humaneval.json", "humaneval2.json"):
    pieces += [r["row"]["prompt"] for r in json.load(open(f"{data}/{name}"))["rows"]]
needle = "Note for the archive: the access code of the blue storage room is 4817-RAVEN."
parts, n, i = [], 0, 0
while n < want * 3.3:                        # ~3.3 characters per token for this mix
    parts.append(f"[Item {i}] {pieces[i % len(pieces)]}")
    n += len(parts[-1]); i += 1
parts.insert(len(parts) // 2, needle)
prompt = "\n\n".join(parts) + "\n\nQuestion: what is the access code of the blue storage room? Answer with the code only."
body = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0, "max_tokens": 20,
        "chat_template_kwargs": {"enable_thinking": False}}
start = time.time()
r = json.load(urllib.request.urlopen(urllib.request.Request(url + "/chat/completions", json.dumps(body).encode(),
                                     {"Content-Type": "application/json"}), timeout=3600))
used = r["usage"]["prompt_tokens"]
answer = r["choices"][0]["message"]["content"] or ""
print(f"needle at {used:,} prompt tokens: {time.time() - start:.0f} s, answer {answer.strip()!r} -> "
      f"{'RIGHT' if '4817' in answer and 'RAVEN' in answer.upper() else 'wrong'}")
