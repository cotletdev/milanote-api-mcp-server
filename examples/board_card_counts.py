#!/usr/bin/env python3
"""Count the cards on each of your Milanote boards, by type, biggest board first.

python board_card_counts.py
python board_card_counts.py --parent 1XiqwC1Mir4d4N --out counts.csv

Also prints the account's use of the free plan's card limit.
"""

import argparse
import sys
from collections import Counter

from milanote_api_mcp.scripting import call, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--parent", help="Count the boards inside this board. Default: the boards on your Home")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    rows = []
    for board in call("list_boards", {"parent_board_id": args.parent, "limit": 200})["boards"]:
        cards = call("get_board", {"board_id": board["id"]})["cards"]
        types = Counter(card["type"] for card in cards)
        rows.append({"board": board["title"], "cards": len(cards), **dict(types), "url": board["url"]})
    rows.sort(key=lambda row: row["cards"], reverse=True)
    write_rows(rows, args.out)
    usage = call("get_usage")
    limit = "no limit" if usage["unlimited"] else f"of {usage['limit']}"
    print(f"Cards used: {usage['used']} {limit}", file=sys.stderr)


if __name__ == "__main__":
    run(main)
