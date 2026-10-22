#!/usr/bin/env python3
"""Turn on a Milanote board's read-only link and print it, or turn it off again.

python publish_board.py --board 1XiqwC1Mir4d4N
python publish_board.py --board 1XiqwC1Mir4d4N --comments --no-downloads
python publish_board.py --board 1XiqwC1Mir4d4N --off

Anyone with the link can view the board. Editors you invited keep their access either way.
"""

import argparse
import json

from milanote_api_mcp.scripting import call, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--board", required=True, help="Board ID or URL")
    parser.add_argument("--comments", action="store_true", help="Let viewers of the link comment")
    parser.add_argument("--no-downloads", action="store_true", help="Hide download links on files")
    parser.add_argument("--off", action="store_true", help="Turn the read-only link off")
    args = parser.parse_args()

    if args.off:
        result = call("unpublish_board", {"board_id": args.board})
    else:
        params = {"board_id": args.board, "allow_comments": args.comments, "allow_downloads": not args.no_downloads}
        result = call("publish_board", params)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run(main)
