#!/usr/bin/env python3
"""Add a to-do list with due dates to a Milanote board from a text file.

python add_todo_list.py --board 1XiqwC1Mir4d4N --title "Client call 22 Oct" --file actions.txt

One task per line. A line may start with a date and an optional time:
    2026-10-28 Send the revised brief
    2026-10-30 14:00 Review call with Anna
    Book the photographer
A date alone means 5 PM that day in your browser's time zone, as in Milanote.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any

from milanote_api_mcp.scripting import call, run

_LINE = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:\s+(\d{1,2}:\d{2}))?\s+(.+)$")


def task(line: str) -> dict[str, Any]:
    found = _LINE.match(line)
    if not found:
        return {"text": line}
    day, at, text = found.groups()
    return {"text": text, "due_date": day, **({"due_time": at.zfill(5)} if at else {})}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--board", required=True, help="Board ID or URL")
    parser.add_argument("--file", required=True, help="Text file, one task per line")
    parser.add_argument("--title", help="List title")
    args = parser.parse_args()

    lines = [line.strip("-* \t") for line in Path(args.file).read_text(encoding="utf-8").splitlines()]
    tasks = [task(line) for line in lines if line]
    result = call("add_todo_list", {"board_id": args.board, "title": args.title, "tasks": tasks})
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run(main)
