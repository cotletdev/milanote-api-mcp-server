"""Remove editor."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import EDITOR, board, board_id, board_url, call

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "user_id": {"type": "string", "description": "Their user_id from get_sharing or invite_editor."},
        "email": {"type": "string", "description": "Their email address, instead of user_id."},
    },
    "required": ["board_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "board_id": "1XiqwC1Mir4d4N",
    "removed_user_id": "6ad4c6a152905d94d7495d08",
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


@tool(
    name="remove_editor",
    title="Remove editor",
    access="write",
    confirm=True,
    description="Take away someone's access to a board, or cancel an invite they have not accepted.",
    details=(
        "Removes one editor, by user_id or email, as the Share dialog's Remove does. They lose the board and "
        "the boards inside it unless a parent board is shared with them too; Milanote does not tell them. "
        "The owner cannot be removed. invite_editor adds them back. By default you confirm each call; you "
        "can switch that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="DELETE /boards/{board_id}/editors",
    example_response=EXAMPLE_RESPONSE,
)
async def remove_editor(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    acl = (await board(ctx, bid))["elements"][bid].get("acl") or {}
    editors = [uid for uid, bits in acl.items() if bits == EDITOR]
    wanted = str(args.get("user_id") or "").strip()
    email = str(args.get("email") or "").strip().lower()
    if not wanted and email and editors:
        users = (await call(ctx, "GET", "/api/users", params={"ids": ",".join(editors)})).get("users") or {}
        wanted = next((uid for uid, u in users.items() if (u.get("email") or "").lower() == email), "")
    if not wanted and not email:
        raise ToolError("Give user_id or email.", ErrorCode.INVALID_INPUT)
    if wanted not in editors:
        raise ToolError("That person is not an editor of this board; get_sharing lists them.", ErrorCode.INVALID_INPUT)
    body = {"removeUserIds": [wanted], "updateUserIds": []}
    await call(ctx, "PUT", f"/api/elements/{bid}/permissions", body=body)
    return {"board_id": bid, "removed_user_id": wanted, "board_url": board_url(bid)}
