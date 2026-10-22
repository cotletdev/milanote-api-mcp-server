"""Set card color."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board, board_id, board_url, element, update

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

# The colour bar swatches of Milanote's Color tool (18.10.2026); a card stores the name.
COLORS = ["grey", "cyan", "green", "brown", "yellow", "orange", "red", "pink", "purple", "blue", "deep_blue"]
_COLORED = {"CARD", "TASK_LIST", "LINK", "COLUMN", "FILE"}

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "card_id": {
            "type": "string",
            "description": "Card ID from get_board: a note, to-do list, link, file or column.",
        },
        "color": {"type": "string", "enum": [*COLORS, "none"], "description": "Colour, or none to clear it."},
    },
    "required": ["board_id", "card_id", "color"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "card_id": "1Xitbu1Mitsmc7",
    "board_id": "1XiqwC1Mir4d4N",
    "color": "red",
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


@tool(
    name="set_card_color",
    title="Set card color",
    access="write",
    confirm=False,
    description="Colour the bar on top of a note, to-do list, link, file or column, or clear it.",
    details=(
        "Sets one of Milanote's eleven card colours, as the Color tool does; none removes it. Boards and "
        "images take no colour here. Editors of the board see the change at once."
    ),
    input_schema=INPUT_SCHEMA,
    route="PUT /boards/{board_id}/cards/{card_id}/color",
    example_response=EXAMPLE_RESPONSE,
)
async def set_card_color(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    color = str(args.get("color") or "").strip().lower()
    if color not in (*COLORS, "none"):
        raise ToolError(f"color must be one of: {', '.join(COLORS)}, none.", ErrorCode.INVALID_INPUT)
    found = element(await board(ctx, bid), bid, args.get("card_id"))
    if found.get("elementType") not in _COLORED:
        raise ToolError("This kind of card takes no colour.", ErrorCode.INVALID_INPUT)
    await update(ctx, bid, found["_id"], {"color": None if color == "none" else color.upper()})
    return {"card_id": found["_id"], "board_id": bid, "color": color, "board_url": board_url(bid)}
