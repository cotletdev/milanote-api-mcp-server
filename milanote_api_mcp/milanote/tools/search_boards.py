"""Search boards."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import LOCALE, board_url, call, card_type, iso

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

_SORTS = {"last_viewed": "viewed", "last_modified": "modified"}
_HIT = re.compile(r"\[/?hit\]")

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Text to look for."},
        "sort": {
            "type": "string",
            "enum": ["last_viewed", "last_modified"],
            "description": "last_viewed or last_modified. Default: last_viewed.",
        },
    },
    "required": ["query"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "total_boards": 2,
    "results": [
        {
            "board_id": "1XiqwC1Mir4d4N",
            "board_title": "Q1 campaign",
            "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
            "path": ["Home"],
            "modified_at": "2026-10-18T15:12:47+02:00",
            "matches": [{"card_id": "1Xiqxr1scDecaq", "type": "note", "snippet": "Palette: warm greys"}],
        },
        {
            "board_id": "1XiqZb1scDec7f",
            "board_title": "Brand refresh",
            "board_url": "https://app.milanote.com/1XiqZb1scDec7f",
            "path": ["Home", "Clients"],
            "modified_at": "2026-10-17T11:40:02+02:00",
            "matches": [],
        },
    ],
}


@tool(
    name="search_boards",
    title="Search boards",
    access="read",
    confirm=False,
    description="Find boards and cards by text across your boards, like the Search icon in Milanote.",
    details=(
        "Runs Milanote's own search over every board you can open. Each result is a board, with the cards on "
        "it that matched (matches) and the boards above it (path). A board whose title matched has no "
        "matches. Sorted by when you last viewed the board, or last modified. Returns Milanote's first page "
        "of boards; use get_board on a result to read all its cards."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /boards/search",
    example_response=EXAMPLE_RESPONSE,
)
async def search_boards(ctx: ToolContext, args: dict[str, Any]) -> Any:

    query = str(args.get("query") or "").strip()
    if not query:
        raise ToolError("query must not be empty.", ErrorCode.INVALID_INPUT)
    sort = _SORTS[args.get("sort") or "last_viewed"]
    params = {"query": query, "offset": 0, "sort": sort, "locale": LOCALE}
    answer = await call(ctx, "GET", "/api/boards/search", params=params)
    tz = ctx.profile.timezone
    results = []
    for row in answer.get("results") or []:
        found = row.get("board") or {}
        bid = row.get("_id") or found.get("_id")
        results.append(
            {
                "board_id": bid,
                "board_title": (found.get("content") or {}).get("title") or "",
                "board_url": board_url(bid),  # pyright: ignore[reportArgumentType]  # every search hit has an _id
                "path": [a.get("title") or "" for a in row.get("ancestors") or []],
                "modified_at": iso(row.get("modifiedTime"), tz),
                "matches": [
                    {
                        "card_id": hit.get("_id"),
                        "type": card_type(hit),
                        "snippet": " ".join(_HIT.sub("", part) for part in hit.get("content") or []),
                    }
                    for hit in row.get("innerHits") or []
                ],
            }
        )
    return {"total_boards": answer.get("total", len(results)), "results": results}
