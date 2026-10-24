# Harness benchmark: which coding agent gets the most out of a local model?

Five small agentic coding tasks, each in its own workspace, with hidden tests that decide afterwards whether the
result is right. Every harness gets the same prompt in a fresh copy of the workspace; the model server is the same
for all of them. Results: [../docs/harness-comparison.md](../docs/harness-comparison.md).

| Task | Kind | The harness has to … | Hidden tests check |
|---|---|---|---|
| `pager` | bug fix | find two bugs (off-by-one, wrong page count) from failing tests | edge cases (empty, exact multiples, out of range); visible tests unchanged |
| `todo` | feature | implement the rest of a CLI as its README describes, and write unit tests | exact output, exit code and stderr of every command; its own tests pass |
| `shop` | multi-file refactor | rename a function across a package, add a keyword-only tax parameter, change a receipt format, update tests | no trace of the old name, keyword-only, rounding, receipt lines; its tests pass |
| `logreport` | script from a spec | write a report over an access log with malformed lines, in an exact output format | exact output on a different, unseen log |
| `pairs` | performance | make an O(n³) function fast without changing results | 300 random cases against a reference, 200k numbers in < 2 s; visible tests unchanged |

## Running it

    python3 run.py                               # all harnesses, all tasks, one round
    python3 run.py --harness opencode --tasks shop,pairs --reps 3 --label mytest
    python3 show.py LABEL [--follow]

Each run happens in a [bubblewrap](https://github.com/containers/bubblewrap) sandbox: the system read-only, writable
only the run folder (the workspace and a fresh home for the harness), so the harnesses run with all permissions
(`--yolo`, `--auto`, `--dangerously-skip-permissions`) but cannot touch anything else, and nothing from earlier
sessions (memories, settings, history) leaks in. Tokens and model calls come from vLLM's `/metrics`; one line per
run goes to `results.jsonl`, the run folders (workspace after the run, harness output, hidden test output) to
`runs/LABEL/`.

How the harnesses reach the local model (vLLM on 127.0.0.1:8000):

| Harness | Connection | Thinking |
|---|---|---|
| Qwen Code | its `settings.json` (copied from `~/.qwen`): OpenAI-compatible provider `local` | `reasoningEffort: xhigh` |
| OpenCode | `opencode.json` in the fresh home: provider `@ai-sdk/openai-compatible`, model `local/local`; `--standalone` (the background service is not reachable from the sandbox) | template default (`xhigh`) |
| Claude Code | `ANTHROPIC_BASE_URL=http://127.0.0.1:8000` (vLLM serves the Anthropic Messages API), all model tiers mapped to `local` | `--effort xhigh` (its default `high` is not one of the model's levels) |

Results of the 2026-10-24 comparison (one line per run, and the blind review scores): [results/](results/).
`export_diffs.py LABEL DIR` writes the anonymous diffs for such a review.

Timeout 15 minutes per run. The tasks use only the Python standard library (`unittest`); `tasks/logreport` has the
generator (`make_log.py`) and the reference solution of its logs.
