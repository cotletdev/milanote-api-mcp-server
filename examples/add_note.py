#!/usr/bin/env python3
"""Add a note card to a Milanote board from text, a file or standard input.

python add_note.py --board 1XiqwC1Mir4d4N --text "Kickoff moved to Tuesday."
python add_note.py --board 1XiqwC1Mir4d4N --file meeting-notes.md
pbpaste | python add_note.py --board 1XiqwC1Mir4d4N

Each line becomes a paragraph. The card lands in the board's Unsorted panel.
"""

import argparse
import json
import sys
from pathlib import Path

from milanote_api_mcp.scripting import call, run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--board", required=True, help="Board ID or URL")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text", help="Note text")
    source.add_argument("--file", help="Read the note from a file")
    args = parser.parse_args()

    if args.text is not None:
        text = args.text
    elif args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()
    print(json.dumps(call("add_note", {"board_id": args.board, "text": text}), indent=2))


if __name__ == "__main__":
    run(main)
