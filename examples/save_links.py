#!/usr/bin/env python3
"""Save a list of links to a Milanote board as link cards, skipping the ones already on it.

python save_links.py --board 1XiqwC1Mir4d4N --file links.txt
python save_links.py --board 1XiqwC1Mir4d4N https://example.com/a https://example.com/b --dry-run

One URL per line in the file. URLs are compared without utm_* parameters and a trailing slash.
New cards land in the board's Unsorted panel. A free Milanote account stops at 100 cards.
"""

import argparse
import json
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from milanote_api_mcp.core.errors import ToolError
from milanote_api_mcp.scripting import call, run


def clean(url: str) -> str:
    parts = urlsplit(url.strip())
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith("utm_")])
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), query, ""))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--board", required=True, help="Board ID or URL")
    parser.add_argument("--file", help="Text file with one URL per line")
    parser.add_argument("urls", nargs="*", help="URLs to save")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be added, add nothing")
    args = parser.parse_args()

    urls = list(args.urls)
    if args.file:
        urls += [line.strip() for line in Path(args.file).read_text(encoding="utf-8").splitlines()]
    urls = [u for u in urls if u.startswith(("http://", "https://"))]
    board = call("get_board", {"board_id": args.board})
    seen = {clean(card["url"]) for card in board["cards"] if card.get("url")}
    added, skipped, failed = [], [], []
    for url in urls:
        if clean(url) in seen:
            skipped.append(url)
            continue
        seen.add(clean(url))
        if args.dry_run:
            added.append(url)
            continue
        try:
            card = call("add_link", {"board_id": board["board_id"], "url": url})
            added.append(card.get("title") or url)
        except ToolError as err:
            failed.append(f"{url}: {err}")
            if "limit" in str(err).lower():
                break
    print(json.dumps({"board": board["title"], "added": added, "skipped": skipped, "failed": failed}, indent=2))


if __name__ == "__main__":
    run(main)
