# Local LLMs on the NVIDIA RTX Spark (N1X): vLLM setup, fixes and benchmarks

Running large local models with vLLM on an NVIDIA RTX Spark N1X laptop: how fast Qwen3.8 27B and Qwen3.8
Flash-Next (MoE) generate and read prompts, what speculative decoding (MTP, DFlash) brings, how far the context
goes, whether quality holds up, which coding harness gets the most out of the model, and the fixes it took to make a
96 GB model start reliably on 128 GB of memory that CPU and GPU share.

Measured on an ASUS ProArt P16 (H7607BA: RTX Spark N1X, 128 GB LPDDR5X, Ubuntu 26.04, October 2026). The N1X
is the same chip family as NVIDIA's DGX Spark (GB10), so most of this applies there too. Getting Linux itself
right on the laptop (drivers, audio, sleep, touchpad) is a separate project:
[proart-p16-linux](https://github.com/LeonMarzollDev/proart-p16-linux).

## Results in short

| Model / preset | Generation | 30k prompt: new / again | Quality (code · tools · math) | Needs |
|---|---|---|---|---|
| **Qwen3.8 Flash-Next** (MoE, MTP×3) | **~60 tok/s** (code 62–65) | **12.3 s / 0.15 s** | **97.5 % · 93 % · 98 %** | ~87 GiB: everything else must pause; ~5 min start |
| Qwen3.8 27B, DFlash2×10 ("fast") | 35.1 tok/s (code 64.3) | 15.7 s / 5.8 s | 95 % · 88 % · 96 % (×12) | ~45–63 GiB |
| Qwen3.8 27B, MTP×4 ("agents") | 32.0 tok/s (code 36.8) | 16.4 s / 1.9 s | 95 % · 88 % · 98 % | ~40–63 GiB |

All numbers, the method and the explanations are in [docs/benchmarks.md](docs/benchmarks.md); the comparison of
coding harnesses (Qwen Code, OpenCode, Claude Code on the local model) in
[docs/harness-comparison.md](docs/harness-comparison.md).

## The fixes that matter on unified memory

CPU and GPU share one memory, and the NVIDIA driver takes GPU memory straight from RAM. What made Flash-Next
(96 GB on disk, ~87 GiB loaded) go from "fails most of the time, 10 minutes" to "starts every time, 5 minutes":

| Fix | Why |
|---|---|
| `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` | repacking the MoE weights after loading piled up freed GPU memory past 100 GiB with the default allocator; with it the phase peaks at ~83 GiB |
| GPU via CDI (`--device nvidia.com/gpu=all`) instead of `--gpus all` | with `--gpus all`, any systemd reload (snap refresh, apt upgrade) takes the GPU away from running containers: `NVMLError_Unknown`, CUDA `operation not permitted` |
| Pin the container to the fast cores (`--cpuset-cpus`) | loading is one Python thread over 375k tensors; Linux kept it on the slow cores. Weights 445 → 146 s |
| Empty the NVIDIA driver's memory pool (`drop_caches`) before loading and after unloading | the driver keeps freed GPU memory (`KReclaimable`, 71–81 GB seen) and does not hand it back in time for the next model |
| Drop the model files from the file cache while loading (`posix_fadvise DONTNEED`) | the driver does not wait for Linux to free 72 GB of just-read file cache |
| `B12X_COMPILE_WORKERS=3`, share 0.76, one 262k conversation, a RAM watchdog | first-start autotuning compilers live outside vLLM's share; ~19 GiB stay free for the desktop |

## What is here

| Path | What |
|---|---|
| [docs/benchmarks.md](docs/benchmarks.md) | speed, prefill and prompt cache, memory and context (up to 1M), quality, MTP draft counts, the start-up fixes in detail |
| [docs/harness-comparison.md](docs/harness-comparison.md) | Qwen Code vs. OpenCode vs. Claude Code on the same local model and tasks |
| [scripts/llm](scripts/llm) | start / stop one model at a time (presets `flash`, `27b-fast`, `27b-agent`, `27b`), all fixes above built in |
| [scripts/llm-indicator](scripts/llm-indicator) | GNOME top-bar menu: load / stop models, loading countdown, speed test |
| [scripts/llm-evict-cache](scripts/llm-evict-cache) | drops the model files from the page cache while a model loads |
| [scripts/llm-swap-reset](scripts/llm-swap-reset) | root helper: `drop_caches` (file cache + driver pool) and an empty swap; with a sudo rule for exactly this file |
| [bench/](bench/) | the measurement scripts: speed, prefill, context fill, needle in a haystack, quality (HumanEval, BFCL, GSM8K) |
| [harness-bench/](harness-bench/) | five agentic coding tasks with hidden tests and a sandboxed runner for coding harnesses |

## Using the scripts

Requirements: Docker (29+) with the NVIDIA Container Toolkit (1.20+, which generates the CDI spec at boot via
`nvidia-cdi-refresh`), the models in `~/models` (`Qwen3.8-Flash-Next-FP4-Local`, `Qwen3.8-27B-NVFP4`,
`Qwen3.8-27B-DFlash2`), Python 3 with GTK and AyatanaAppIndicator for the menu.

    install -m 0755 scripts/llm scripts/llm-indicator scripts/llm-evict-cache ~/.local/bin/
    sudo install -o root -g root -m 0755 scripts/llm-swap-reset /usr/local/sbin/llm-swap-reset
    # edit the user name in scripts/llm-swap-reset.sudoers.example, then:
    sudo visudo -cf scripts/llm-swap-reset.sudoers.example && \
        sudo install -o root -g root -m 0440 scripts/llm-swap-reset.sudoers.example /etc/sudoers.d/llm-swap-reset

    llm start flash        # Flash-Next, ~5 min; OpenAI API (and Anthropic /v1/messages) on 127.0.0.1:8000
    llm status | logs | stop
    LLM_BENCH=$PWD/bench/bench.py llm bench    # speed test of the loaded model (default path: ~/llm/bench.py)

The scripts pause and resume "Spark", the author's local voice assistant (three small models on the GPU), through
`~/.local/bin/voice on|off`; without that script those steps do nothing. Without the sudo rule the memory
clean-up is skipped, and big models start less reliably.

## License

MIT, see [LICENSE](LICENSE).
