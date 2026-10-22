"""Trash cards."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board, board_id, board_url, element, sync, trash

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

MAX_CARDS = 50

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "card_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": f"1 to {MAX_CARDS} card IDs from get_board; a sub-board's board_id works too.",
        },
    },
    "required": ["board_id", "card_ids"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "board_id": "1XiqwC1Mir4d4N",
    "trashed": ["1Xit9D1Y0ZjyeS", "1Xitbu1Mitsmc7"],
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


@tool(
    name="trash_cards",
    title="Trash cards",
    access="write",
    confirm=True,
    description="Move cards or sub-boards to the trash, as the Delete key does.",
    details=(
        "The cards leave the board for everyone who can see it, and a trashed sub-board takes its contents "
        "with it. Nothing is gone for good: list_trash shows them and restore_card puts one back where it "
        "was, until the trash is emptied in Milanote. By default you confirm each call; you can switch that "
        "off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /boards/{board_id}/cards/trash",
    example_response=EXAMPLE_RESPONSE,
)
async def trash_cards(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    ids = [str(i).strip() for i in args.get("card_ids") or [] if str(i).strip()]
    if not 1 <= len(ids) <= MAX_CARDS:
        raise ToolError(f"card_ids must hold 1 to {MAX_CARDS} IDs.", ErrorCode.INVALID_INPUT)
    answer = await board(ctx, bid)
    found = [element(answer, bid, i)["_id"] for i in dict.fromkeys(ids)]
    _, link = await sync(ctx)
    await trash(ctx, link, found, answer)
    await link.close()
    return {"board_id": bid, "trashed": found, "board_url": board_url(bid)}
