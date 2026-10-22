"""Rename board."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board, board_id, board_url, update

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "title": {"type": "string", "description": "New title."},
    },
    "required": ["board_id", "title"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "board_id": "1XiqwC1Mir4d4N",
    "title": "Spring shoot, final",
    "previous_title": "Spring shoot",
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


@tool(
    name="rename_board",
    title="Rename board",
    access="write",
    confirm=False,
    description="Change a board's title.",
    details=(
        "Renames the board everywhere it shows: its card on the parent board, the breadcrumb and search. "
        "The board_id and the links to it stay the same. Your Home cannot be renamed."
    ),
    input_schema=INPUT_SCHEMA,
    route="PATCH /boards/{board_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def rename_board(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    title = str(args.get("title") or "").strip()
    if not title:
        raise ToolError("title must not be empty.", ErrorCode.INVALID_INPUT)
    found = (await board(ctx, bid))["elements"][bid]
    location = found.get("location") or {}
    if location.get("rootBoard"):
        raise ToolError("Home and Quick notes cannot be renamed.", ErrorCode.INVALID_INPUT)
    previous = (found.get("content") or {}).get("title") or ""
    await update(ctx, location.get("parentId") or bid, bid, {"title": title})
    return {"board_id": bid, "title": title, "previous_title": previous, "board_url": board_url(bid)}
