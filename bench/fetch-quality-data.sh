#!/bin/sh
# Downloads the test data of quality.py into bench/quality-data: HumanEval (164 problems), GSM8K (first 100 of the
# test split) from the Hugging Face datasets server, and BFCL v3 simple / multiple / parallel with their answers.
set -e
D="$(dirname "$0")/quality-data"
mkdir -p "$D"
rows="https://datasets-server.huggingface.co/rows"
curl -sfL -m 60 -o "$D/humaneval.json"  "$rows?dataset=openai/openai_humaneval&config=openai_humaneval&split=test&offset=0&length=100"
curl -sfL -m 60 -o "$D/humaneval2.json" "$rows?dataset=openai/openai_humaneval&config=openai_humaneval&split=test&offset=100&length=64"
curl -sfL -m 60 -o "$D/gsm8k.json"      "$rows?dataset=openai/gsm8k&config=main&split=test&offset=0&length=100"
bfcl="https://huggingface.co/datasets/gorilla-llm/Berkeley-Function-Calling-Leaderboard/resolve/main"
for f in BFCL_v3_simple.json BFCL_v3_multiple.json BFCL_v3_parallel.json possible_answer/BFCL_v3_simple.json \
         possible_answer/BFCL_v3_multiple.json possible_answer/BFCL_v3_parallel.json; do
    curl -sfL -m 60 -o "$D/$(echo "$f" | tr / _)" "$bfcl/$f"
done
ls -l "$D"
