"""Move card."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board, board_id, board_url, children, element, move, sync, unsorted

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board the card is on now: ID or board URL."},
        "card_id": {"type": "string", "description": "Card ID from get_board; a sub-board's board_id works too."},
        "to_board_id": {"type": "string", "description": "Board to move it to. Default: the same board."},
        "to_column_id": {
            "type": "string",
            "description": "Column on the target board to put it in, at the top. Default: no column.",
        },
    },
    "required": ["board_id", "card_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "card_id": "1Xit9D1Y0ZjyeS",
    "from_board_id": "1XiqwC1Mir4d4N",
    "board_id": "1XiqC51scDec9a",
    "column_id": None,
    "section": "unsorted",
    "board_url": "https://app.milanote.com/1XiqC51scDec9a",
}


@tool(
    name="move_card",
    title="Move card",
    access="write",
    confirm=False,
    description="Move a card or a sub-board to another board, or into or out of a column.",
    details=(
        "Moves it the way drag and drop does, keeping its ID, comments and content. With to_column_id it goes "
        "to the top of that column; without it, to the top of the target board's Unsorted panel. Moving a "
        "board moves everything inside it. Moving to a board shared with other people shows it to them."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /boards/{board_id}/cards/{card_id}/move",
    example_response=EXAMPLE_RESPONSE,
)
async def move_card(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    found = element(await board(ctx, bid), bid, args.get("card_id"))
    target = board_id(args["to_board_id"], "to_board_id") if args.get("to_board_id") else bid
    if target == found["_id"]:
        raise ToolError("A board cannot move into itself.", ErrorCode.INVALID_INPUT)
    answer = await board(ctx, target)
    column = str(args.get("to_column_id") or "").strip() or None
    if column:
        kids = [e for e in children(answer, target) if e["_id"] == column and e.get("elementType") == "COLUMN"]
        if not kids:
            raise ToolError("to_column_id is not a column on the target board.", ErrorCode.INVALID_INPUT)
        top = min(
            (
                float(((e.get("location") or {}).get("position") or {}).get("score") or 0)
                for e in children(answer, target)
                if (e.get("location") or {}).get("parentId") == column
            ),
            default=1.0,
        )
        location = {"parentId": column, "section": "INBOX", "position": {"index": 0, "score": top - 1}}
    else:
        location = unsorted(answer, target)
    _, link = await sync(ctx)
    await move(link, [{"id": found["_id"], "location": location, "from": found.get("location") or {}}])
    await link.close()
    return {
        "card_id": found["_id"],
        "from_board_id": bid,
        "board_id": target,
        "column_id": column,
        "section": "column" if column else "unsorted",
        "board_url": board_url(target),
    }
