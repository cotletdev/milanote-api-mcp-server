"""Duplicate board."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board, board_id, board_url, call, sync, unsorted

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

# What the web app copies onto the new board element before the server copies the contents (18.10.2026).
_KEEP = ("title", "icon", "color", "secondaryColor", "defaultColorPalette")
# Milanote acks the new board before every server sees it: one test run in four got this answer to the
# duplicate request right after the ack (20.10.2026), and the same request a moment later succeeds.
_NOT_SEEN_YET = "JSON element definition"
_TRIES, _WAIT_S = 4, 1.5

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board to copy: ID or board URL."},
        "title": {"type": "string", "description": "Title of the copy. Default: the same title."},
        "parent_board_id": {
            "type": "string",
            "description": "Board to put the copy in (ID or board URL). Default: where the original is.",
        },
    },
    "required": ["board_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "board_id": "1Xitig1OONUbdP",
    "original_board_id": "1XiqwC1Mir4d4N",
    "title": "Spring shoot",
    "parent_board_id": "1XiqvH1OOLn08n",
    "card_count": 4,
    "board_url": "https://app.milanote.com/1Xitig1OONUbdP",
}


@tool(
    name="duplicate_board",
    title="Duplicate board",
    access="write",
    confirm=False,
    description="Copy a board with everything on it, sub-boards included, as a template.",
    details=(
        "Does what Duplicate in a board's menu does: Milanote copies every card, column, comment and "
        "sub-board into a new board and returns its board_id. The copy lands in the parent board's Unsorted "
        "panel, private to you unless that board is shared; the read-only link and editors are not copied. "
        "Every copied card counts toward the free plan's card limit (get_usage). card_count is what "
        "Milanote reports it copied."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /boards/{board_id}/duplicate",
    example_response=EXAMPLE_RESPONSE,
)
async def duplicate_board(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    original = (await board(ctx, bid))["elements"][bid]
    if (original.get("location") or {}).get("rootBoard"):
        raise ToolError("Home and Quick notes cannot be duplicated.", ErrorCode.INVALID_INPUT)
    content = {key: (original.get("content") or {}).get(key) for key in _KEEP}
    if str(args.get("title") or "").strip():
        content["title"] = str(args["title"]).strip()
    parent = (
        board_id(args["parent_board_id"], "parent_board_id")
        if args.get("parent_board_id")
        else (original.get("location") or {}).get("parentId")
    )
    # A board that is not a root board always has a parentId.
    location = unsorted(await board(ctx, parent), parent)  # pyright: ignore[reportArgumentType]
    _, link = await sync(ctx)
    new_id = link.new_id()
    await link.create(new_id, "BOARD", location, content)
    await link.close()
    body = {
        "duplications": [
            {"originalElementId": bid, "newElementId": new_id, "newElementLocation": location, "elementType": "BOARD"}
        ]
    }
    answer = await _duplicate(ctx, body)
    counts = answer.get("elementCount") or {}
    return {
        "board_id": new_id,
        "original_board_id": bid,
        "title": content.get("title") or "",
        "parent_board_id": parent,
        "card_count": sum(v for v in counts.values() if isinstance(v, int)),
        "board_url": board_url(new_id),
    }


async def _duplicate(ctx: ToolContext, body: dict[str, Any]) -> Any:
    for attempt in range(_TRIES):
        try:
            return await call(ctx, "POST", "/api/elements/duplicate", body=body)
        except ToolError as exc:
            if _NOT_SEEN_YET not in str(exc) or attempt == _TRIES - 1:
                raise
        await asyncio.sleep(_WAIT_S)
    return None
