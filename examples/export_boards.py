#!/usr/bin/env python3
"""Export a Milanote board and its sub-boards to files, one file per board, folders following the nesting.

python export_boards.py --board 1XiqwC1Mir4d4N --dir ./outline
python export_boards.py --board https://app.milanote.com/1XiqwC1Mir4d4N --format plain_text --depth 1

Markdown and plain text are written from the tool's answer. Word, PDF and PNG are downloaded from file_url
while your session is valid. A second run overwrites the same paths, so a git diff shows what changed.
"""

import argparse
import re
import urllib.request
from pathlib import Path

from milanote_api_mcp.scripting import call, run

_EXT = {"markdown": "md", "plain_text": "txt", "word": "docx", "pdf": "pdf", "png": "png"}


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:80] or "board"


def export(board_id: str, folder: Path, fmt: str, depth: int) -> int:
    board = call("get_board", {"board_id": board_id})
    name = slug(board["title"])
    result = call("export_board", {"board_id": board_id, "format": fmt})
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.{_EXT[fmt]}"
    if "content" in result:
        path.write_text(result["content"], encoding="utf-8")
    else:
        with urllib.request.urlopen(result["file_url"], timeout=60) as response:
            path.write_bytes(response.read())
    print(f"{path} ({len(board['cards'])} cards)")
    count = 1
    if depth > 0:
        for card in board["cards"]:
            if card["type"] == "board":
                count += export(card["board_id"], folder / name, fmt, depth - 1)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--board", required=True, help="Board ID or URL")
    parser.add_argument("--dir", default=".", help="Folder to write into. Default: here")
    parser.add_argument("--format", choices=list(_EXT), default="markdown")
    parser.add_argument("--depth", type=int, default=5, help="Levels of sub-boards to export. 0: only this board")
    args = parser.parse_args()

    total = export(args.board, Path(args.dir), args.format, args.depth)
    print(f"Exported {total} boards")


if __name__ == "__main__":
    run(main)
