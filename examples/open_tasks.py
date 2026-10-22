#!/usr/bin/env python3
"""List the unticked tasks of every to-do list on a Milanote board and its sub-boards, soonest due first.

python open_tasks.py --board 1XiqwC1Mir4d4N
python open_tasks.py --board 1XiqwC1Mir4d4N --due-before 2026-11-01 --out tasks.csv
"""

import argparse
from typing import Any

from milanote_api_mcp.scripting import call, run, write_rows


def collect(board_id: str, depth: int) -> list[dict[str, Any]]:
    board = call("get_board", {"board_id": board_id})
    rows = []
    for card in board["cards"]:
        if card["type"] == "todo_list":
            for task in card["tasks"]:
                if not task["done"]:
                    rows.append(
                        {
                            "board": board["title"],
                            "list": card.get("title"),
                            "task": task["text"],
                            "due_date": task.get("due_date"),
                            "due_time": task.get("due_time"),
                            "card_id": card["id"],
                            "task_id": task["task_id"],
                            "board_url": board["url"],
                        }
                    )
        elif card["type"] == "board" and depth > 0:
            rows += collect(card["board_id"], depth - 1)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--board", required=True, help="Board ID or URL")
    parser.add_argument("--depth", type=int, default=3, help="Levels of sub-boards to read. Default: 3")
    parser.add_argument("--due-before", help="Only tasks due before this date (YYYY-MM-DD)")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    rows = collect(args.board, args.depth)
    if args.due_before:
        rows = [row for row in rows if row["due_date"] and row["due_date"] < args.due_before]
    rows.sort(key=lambda row: (row["due_date"] or "9999", row["due_time"] or ""))
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
