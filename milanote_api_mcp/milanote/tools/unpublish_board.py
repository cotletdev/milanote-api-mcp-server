"""Unpublish board."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board, board_id, board_url, call

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."}},
    "required": ["board_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "board_id": "1XiqwC1Mir4d4N",
    "read_only_link": None,
    "was_published": True,
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


@tool(
    name="unpublish_board",
    title="Unpublish board",
    access="write",
    confirm=False,
    description="Turn off a board's read-only link; people who had it can no longer open the board.",
    details=(
        "Does what switching off Share, Enable read-only link does. Editors keep their access. publish_board "
        "turns the same link back on, so anyone who kept it can open the board again. was_published is "
        "false when the board had no link."
    ),
    input_schema=INPUT_SCHEMA,
    route="DELETE /boards/{board_id}/publish",
    example_response=EXAMPLE_RESPONSE,
)
async def unpublish_board(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    content = (await board(ctx, bid))["elements"][bid].get("content") or {}
    was = bool(content.get("published"))
    if was:
        await call(ctx, "DELETE", f"/api/elements/{bid}/publish")
    return {"board_id": bid, "read_only_link": None, "was_published": was, "board_url": board_url(bid)}
