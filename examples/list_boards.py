#!/usr/bin/env python3
"""List your Milanote boards as a tree: title, ID, parent, depth and URL.

python list_boards.py
python list_boards.py --parent 1XiqwC1Mir4d4N --depth 3 --out boards.csv

Without --parent it starts at your Home. Each level below the first is one get_board call.
"""

import argparse
from typing import Any

from milanote_api_mcp.scripting import call, run, write_rows


def walk(parent: str | None, depth: int, max_depth: int) -> list[dict[str, Any]]:
    rows = []
    for board in call("list_boards", {"parent_board_id": parent, "limit": 200})["boards"]:
        rows.append({**board, "depth": depth})
        if depth < max_depth:
            rows += walk(board["id"], depth + 1, max_depth)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--parent", help="Board ID or URL to start from. Default: your Home")
    parser.add_argument("--depth", type=int, default=2, help="How many levels of sub-boards to read. Default: 2")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    write_rows(walk(args.parent, 1, args.depth), args.out)


if __name__ == "__main__":
    run(main)
