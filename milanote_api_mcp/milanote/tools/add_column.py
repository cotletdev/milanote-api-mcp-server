"""Add column."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board, board_id, board_url, sync, unsorted

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "title": {"type": "string", "description": "Column title."},
    },
    "required": ["board_id", "title"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "column_id": "1Xitbl1Mitsmc6",
    "board_id": "1XiqwC1Mir4d4N",
    "title": "Shot list",
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


@tool(
    name="add_column",
    title="Add column",
    access="write",
    confirm=False,
    description="Empty column on a board, to group cards in a stack.",
    details=(
        "Adds a titled column on top of the board's Unsorted panel and returns its column_id; move_card "
        "with to_column_id puts cards into it. Editors of the board see it, nobody is notified."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /boards/{board_id}/columns",
    example_response=EXAMPLE_RESPONSE,
)
async def add_column(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    title = str(args.get("title") or "").strip()
    if not title:
        raise ToolError("title must not be empty.", ErrorCode.INVALID_INPUT)
    location = unsorted(await board(ctx, bid), bid)
    _, link = await sync(ctx)
    column_id = link.new_id()
    await link.create(column_id, "COLUMN", location, {"title": title})
    await link.close()
    return {"column_id": column_id, "board_id": bid, "title": title, "board_url": board_url(bid)}
