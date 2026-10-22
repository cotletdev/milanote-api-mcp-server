"""Edit note."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board, board_id, board_url, doc, element, update

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "card_id": {"type": "string", "description": "Note ID from get_board."},
        "text": {"type": "string", "description": "New note text. Each line becomes a paragraph."},
    },
    "required": ["board_id", "card_id", "text"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "card_id": "1Xit9D1Y0ZjyeS",
    "board_id": "1XiqwC1Mir4d4N",
    "text": "Golden hour at the pier, bring the 85mm and the ND filter.",
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


@tool(
    name="edit_note",
    title="Edit note",
    access="write",
    confirm=False,
    description="Replace the text of a note card.",
    details=(
        "Overwrites the whole note with plain text: line breaks become paragraphs, and bold, links or lists "
        "the note had are lost. Only note cards; to-do lists change with set_task_done. Editors of the board "
        "see the change at once; Milanote's undo in the app does not reach it."
    ),
    input_schema=INPUT_SCHEMA,
    route="PATCH /boards/{board_id}/notes/{card_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def edit_note(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    text = str(args.get("text") or "")
    if not text.strip():
        raise ToolError("text must not be empty.", ErrorCode.INVALID_INPUT)
    found = element(await board(ctx, bid), bid, args.get("card_id"))
    if found.get("elementType") != "CARD":
        raise ToolError("card_id is not a note.", ErrorCode.INVALID_INPUT)
    await update(ctx, bid, found["_id"], {"textContent": doc(text)})
    return {"card_id": found["_id"], "board_id": bid, "text": text, "board_url": board_url(bid)}
