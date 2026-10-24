import re
import sys
from collections import Counter

LINE = re.compile(r'^(\S+) \S+ \S+ \[[^\]]+\] "[^"]*" (\d{3}) (\d+|-)$')
ips, total, errors = Counter(), 0, 0
for line in open(sys.argv[1]):
    m = LINE.match(line.rstrip("\n"))
    if not m:
        continue
    total += 1
    ips[m.group(1)] += 1
    errors += m.group(2).startswith("5")
print(f"requests: {total}")
print("top ips:")
for ip, count in sorted(ips.items(), key=lambda kv: (-kv[1], kv[0]))[:5]:
    print(f"  {ip} {count}")
print(f"server errors: {100 * errors / total:.1f}%")
