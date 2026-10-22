"""Create board."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board, board_content, board_id, board_url, sync, unsorted

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Board title."},
        "parent_board_id": {
            "type": "string",
            "description": "Board to nest it in (ID or board URL). Default: your Home.",
        },
    },
    "required": ["title"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "board_id": "1XiqwC1Mir4d4N",
    "title": "Location scout",
    "parent_board_id": "1XiqvH1OOLn08n",
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


@tool(
    name="create_board",
    title="Create board",
    access="write",
    confirm=False,
    description="New board on your Home or nested inside another board.",
    details=(
        "Creates an empty board and returns its board_id for the tools that add cards. It appears in the "
        "Unsorted panel of the parent board (your Home by default), where you can drag it onto the canvas. "
        "It is private unless the parent board is shared, in which case the parent's editors can open it; "
        "nobody is notified. Move it to the trash in Milanote to undo it."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /boards",
    example_response=EXAMPLE_RESPONSE,
)
async def create_board(ctx: ToolContext, args: dict[str, Any]) -> Any:

    title = str(args.get("title") or "").strip()
    if not title:
        raise ToolError("title must not be empty.", ErrorCode.INVALID_INPUT)
    user, link = await sync(ctx)
    parent = board_id(args["parent_board_id"], "parent_board_id") if args.get("parent_board_id") else None
    parent = parent or user["rootBoardId"]
    location = unsorted(await board(ctx, parent), parent)
    new_id = link.new_id()
    await link.create(new_id, "BOARD", location, board_content(title))
    await link.close()
    return {"board_id": new_id, "title": title, "parent_board_id": parent, "board_url": board_url(new_id)}
