# todo

A tiny todo list. The list is stored as JSON in the file named by the environment variable `TODO_FILE`
(default: `todos.json` in the current directory).

    python3 todo.py add "buy milk"     # prints: added 1
    python3 todo.py list               # all todos
    python3 todo.py list --open        # only the ones not done yet
    python3 todo.py done 1             # marks todo 1 as done, prints: done 1

`list` prints one line per todo, in id order: `1. [ ] buy milk` for an open todo, `2. [x] call Anna` for a done
one. With no matching todos it prints `nothing to do`.

`done` with an id that does not exist prints `no todo with id 7` to standard error and exits with status 1.
Marking a todo that is already done again is fine (prints `done 1` again).
