"""Restore card."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board_url, call, move, sync

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"card_id": {"type": "string", "description": "ID of a trashed card or board from list_trash."}},
    "required": ["card_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "card_id": "1Xit9D1Y0ZjyeS",
    "board_id": "1XiqwC1Mir4d4N",
    "column_id": "1Xitbl1Mitsmc6",
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


@tool(
    name="restore_card",
    title="Restore card",
    access="write",
    confirm=False,
    description="Take a card or board out of the trash and put it back where it was.",
    details=(
        "Puts it back on the board, and in the column, it was trashed from, at its old place; a restored "
        "board comes back with its contents. column_id is set when it went back into a column. Only items in "
        "your own trash, as list_trash shows them."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /trash/{card_id}/restore",
    example_response=EXAMPLE_RESPONSE,
)
async def restore_card(ctx: ToolContext, args: dict[str, Any]) -> Any:

    wanted = str(args.get("card_id") or "").strip()
    answer = await call(ctx, "GET", "/api/users/me/trash", params={"other-users": "false"})
    found = (answer.get("elements") or {}).get(wanted)
    if not found:
        raise ToolError("card_id is not in your trash; list_trash shows what is.", ErrorCode.INVALID_INPUT)
    location = found.get("location") or {}
    back = (location.get("position") or {}).get("restoreLocation") or {}
    if not back.get("parentId"):
        raise ToolError("Milanote does not know where this card came from.", ErrorCode.TARGET_ERROR)
    _, link = await sync(ctx)
    await move(link, [{"id": wanted, "location": back, "from": location}])
    await link.close()
    bid = str(location.get("parentId") or "").removesuffix("-trash") or back["parentId"]
    column = back["parentId"] if back["parentId"] != bid else None
    return {"card_id": wanted, "board_id": bid, "column_id": column, "board_url": board_url(bid)}
