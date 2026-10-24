"""Writes an access log in common log format with a few broken lines (deterministic per seed)."""
import random
import sys

seed, n, path = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
rnd = random.Random(seed)
ips = [f"10.0.{rnd.randint(0, 3)}.{rnd.randint(1, 40)}" for _ in range(60)]
weights = [rnd.random() ** 3 for _ in ips]
paths = ["/", "/login", "/api/items", "/api/items/42", "/static/app.js", "/health"]
with open(path, "w") as f:
    for i in range(n):
        if rnd.random() < 0.01:
            f.write(rnd.choice(["", "garbage line\n"[:-1], "10.0.0.1 - - [bad", "-- truncated --"]) + "\n")
            continue
        ip = rnd.choices(ips, weights)[0]
        status = rnd.choices([200, 201, 304, 404, 500, 502, 503], [70, 5, 10, 8, 3, 2, 2])[0]
        f.write(f'{ip} - - [24/Oct/2026:10:{i // 60 % 60:02d}:{i % 60:02d} +0200] '
                f'"GET {rnd.choice(paths)} HTTP/1.1" {status} {rnd.randint(0, 50000)}\n')
