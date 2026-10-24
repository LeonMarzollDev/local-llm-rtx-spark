# Coding harnesses on the local model: Qwen Code vs. OpenCode vs. Claude Code

> **Preliminary**: the comparison is still running (5 tasks × 3 harnesses × 2 rounds, plus a blind review of the
> code). The table below holds the runs finished so far; this page is updated when it is complete.

Same model for all three: Qwen3.8 Flash-Next (MoE, FP4, MTP×3) served by vLLM on the laptop, thinking at
`xhigh`. Same tasks, same prompts, a fresh sandboxed workspace per run, hidden tests decide. Setup and tasks:
[../harness-bench/](../harness-bench/).

| Harness | Version |
|---|---|
| Qwen Code | 0.26.0 |
| OpenCode | 2.1.4 |
| Claude Code | 2.1.310 |

## Runs so far (round 1)

| Task | Qwen Code | OpenCode | Claude Code |
|---|---|---|---|
| `pager` (bug fix) | pass, 111 s, 9 calls | pass, **45 s**, 11 calls | pass, 61 s, 9 calls |
| `todo` (feature + tests) | pass, 243 s, 14 calls | pass, **110 s**, 12 calls | pass, 132 s, 16 calls |

"calls" = requests to the model; the time is wall-clock from start to the harness exiting, on one laptop with
the desktop in use.
