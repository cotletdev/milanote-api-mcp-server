#!/usr/bin/env python3
"""Search all your Milanote boards for a word or phrase and print where it is.

python search_boards.py "color palette"
python search_boards.py invoice --sort last_modified --out hits.csv
"""

import argparse

from milanote_api_mcp.scripting import call, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("query")
    parser.add_argument("--sort", choices=["last_viewed", "last_modified"], default="last_viewed")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    answer = call("search_boards", {"query": args.query, "sort": args.sort})
    rows = [
        {
            "board": result["board_title"],
            "path": " > ".join(result["path"]),
            "card_id": match["card_id"],
            "type": match["type"],
            "snippet": match["snippet"],
            "board_url": result["board_url"],
        }
        for result in answer["results"]
        for match in result["matches"] or [{"card_id": None, "type": "board", "snippet": ""}]
    ]
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
