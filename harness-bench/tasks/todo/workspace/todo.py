"""A tiny todo list on the command line. See README.md."""
import argparse
import json
import os
import sys


def store_path():
    return os.environ.get("TODO_FILE", "todos.json")


def load():
    try:
        with open(store_path()) as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save(todos):
    with open(store_path(), "w") as f:
        json.dump(todos, f, indent=1)


def cmd_add(args):
    todos = load()
    new_id = max((t["id"] for t in todos), default=0) + 1
    todos.append({"id": new_id, "text": args.text, "done": False})
    save(todos)
    print(f"added {new_id}")


def cmd_list(args):
    for t in load():
        print(f"{t['id']}. {t['text']}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="todo")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("add")
    p.add_argument("text")
    p.set_defaults(func=cmd_add)
    p = sub.add_parser("list")
    p.set_defaults(func=cmd_list)
    args = parser.parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
