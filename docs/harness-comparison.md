# Coding harnesses on the local model: Qwen Code vs. OpenCode vs. Claude Code

Same model for all three: Qwen3.8 Flash-Next (MoE, FP4, MTP×3) served by vLLM on the laptop, thinking on at
`xhigh`. Same five tasks, same prompts, a fresh sandboxed workspace per run, two rounds (30 runs), hidden tests
decide whether a result is right, and a blind review grades the code. Setup and tasks:
[../harness-bench/](../harness-bench/). Measured 2026-10-24.

| Harness | Version | Connection | Thinking |
|---|---|---|---|
| Qwen Code | 0.26.0 | OpenAI API | `reasoningEffort: xhigh` |
| OpenCode | 2.1.4 | OpenAI API (`@ai-sdk/openai-compatible`) | model default (`xhigh`); reasoning tokens in every step |
| Claude Code | 2.1.310 | Anthropic Messages API (vLLM serves `/v1/messages`) | `--effort xhigh` |

## Result in short

| Harness | Hidden tests | Total time (10 runs) | Median per task | Context sent to the model (share from the prompt cache) | Code review (blind, of 10) |
|---|---|---|---|---|---|
| **OpenCode** | **10/10** | 1,532 s | **108 s** | **1.38 M tokens** (92 %) | 7.7 |
| **Claude Code** | **10/10** | **1,445 s** | 116 s | 1.95 M tokens (92 %) | 7.9 |
| Qwen Code | **10/10** | 2,353 s | 198 s | 2.23 M tokens (**67 %**) | 7.8 |

- **All three solve everything**, and the code is equally good: the differences in the review are smaller than
  the scatter within one harness. On this model, quality comes from the model, not from the harness.
- **OpenCode and Claude Code are equally fast** (within 6 % in total; each wins some tasks). **OpenCode sends the
  least context** (~30 % less than Claude Code), which matters as sessions and repositories grow: less to read
  per step and less KV cache.
- **Qwen Code is clearly the slowest** with this model (median 1.8× as long): only 67 % of what it sends comes
  from vLLM's prefix cache (92 % for the others), so more of every step's prompt has to be read again, and it
  generates the most tokens.
- **Single runs scatter a lot**, mostly by how long the model thinks: on `pairs` each harness had one run where
  the model thought for minutes (OpenCode 593 s with 18.5k reasoning tokens in two steps, then 41 s in round 2;
  Claude Code 142 s, then 470 s).

## Per task

Seconds, round 1 / round 2 (all runs passed their hidden tests):

| Task | Kind | OpenCode | Claude Code | Qwen Code |
|---|---|---|---|---|
| `pager` | bug fix | 45 / 96 | 61 / 34 | 111 / 101 |
| `todo` | feature + tests | 110 / 104 | 132 / 101 | 243 / 199 |
| `shop` | multi-file refactor + tests | 132 / 105 | 165 / 91 | 227 / 171 |
| `logreport` | script from a spec | 139 / 167 | 162 / 87 | 214 / 152 |
| `pairs` | performance | 593 / 41 | 142 / 470 | 739 / 196 |

Model calls per run: OpenCode 7–15, Claude Code 5–19, Qwen Code 9–18. Generated tokens in total: OpenCode 71k,
Claude Code 67k, Qwen Code 93k.

## Blind code review

The 30 solutions were exported as diffs under random ids, so nothing showed which harness wrote what. One
reviewer per task scored the six solutions to that task (1–5 for correctness beyond the tests, focus, clarity
and tests; overall of 10).

| Harness | Correctness | Focus | Clarity | Tests | Overall |
|---|---|---|---|---|---|
| OpenCode | 4.6 | 4.5 | 4.1 | 4.4 | 7.7 |
| Claude Code | 4.6 | 4.8 | 4.4 | 4.2 | 7.9 |
| Qwen Code | 4.4 | 4.9 | 4.3 | 4.2 | 7.8 |

Overall per task, round 1 / round 2:

| Task | OpenCode | Claude Code | Qwen Code |
|---|---|---|---|
| `pager` | 10 / 10 | 10 / 10 | 10 / 10 |
| `todo` | 9 / 8 | 9 / 8 | 8 / 9 |
| `shop` | 8 / 7 | 9 / 7 | 6 / 7 |
| `logreport` | 8 / 5 | 7 / 7 | 6 / 8 |
| `pairs` | 6 / 6 | 5 / 7 | 8 / 6 |

What the reviews found:

- `pager`: all six are the same two-line fix (two equivalent ceiling-division idioms).
- `todo`: all implementations correct and minimal; the differences are in the tests (isolation with a temporary
  store, misleading test names, tests of internals).
- `shop`: the best solution keeps all rounding in one place (`pricing.breakdown()` returns net, tax and total);
  the weaker ones repeat the tax formula in the receipt code.
- `logreport`: how strictly a "valid log line" is recognised varies (empty timestamps, trailing fields); one
  solution kept dead code from an abandoned regex (5/10).
- `pairs`: three of six (one per harness) compute `b = target - a` instead of testing `a + b == target`, which is
  exact for integers (all the hidden tests use) but changes results for floating-point input. A reminder that
  "do not change what it returns for any input" needs tests for the inputs you care about.

## Which one to use

With this local model, **OpenCode or Claude Code**. OpenCode has the lighter context and shows tokens per second
for every response (the "TPS" setting under Session, on by default); Claude Code needs `--effort xhigh` (its
default `high` is not one of the model's reasoning levels and the request fails) and the Anthropic endpoint.
Qwen Code works just as correctly but takes about twice as long here.
