"""Add note."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board, board_id, board_url, doc, sync, unsorted

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "text": {"type": "string", "description": "Note text. Each line becomes a paragraph."},
    },
    "required": ["board_id", "text"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "card_id": "1Xiqyn1Mir69e4",
    "board_id": "1XiqwC1Mir4d4N",
    "type": "note",
    "text": "Kickoff moved to Tuesday.",
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


@tool(
    name="add_note",
    title="Add note",
    access="write",
    confirm=False,
    description="Note card with plain text, added to a board's Unsorted panel.",
    details=(
        "Adds one note card on top of the board's Unsorted panel and returns its card_id. The text is plain: "
        "line breaks become paragraphs, Markdown is not converted. On the free plan a note counts toward the "
        "100 cards limit. Editors of the board see it, nobody is notified; move it to the trash in Milanote "
        "to undo it."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /boards/{board_id}/notes",
    example_response=EXAMPLE_RESPONSE,
)
async def add_note(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    text = str(args.get("text") or "")
    if not text.strip():
        raise ToolError("text must not be empty.", ErrorCode.INVALID_INPUT)
    location = unsorted(await board(ctx, bid), bid)
    _, link = await sync(ctx)
    card_id = link.new_id()
    await link.create(card_id, "CARD", location, {"textContent": doc(text)})
    await link.close()
    return {"card_id": card_id, "board_id": bid, "type": "note", "text": text, "board_url": board_url(bid)}
