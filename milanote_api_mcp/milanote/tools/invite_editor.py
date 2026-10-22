"""Invite editor."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import EDITOR, LOCALE, board, board_id, board_url, call, me

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "email": {"type": "string", "description": "Their email address."},
    },
    "required": ["board_id", "email"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "board_id": "1XiqwC1Mir4d4N",
    "invited": "sam@example.com",
    "user_id": "6ad4c6a152905d94d7495d08",
    "role": "editor",
    "status": "invited",
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


@tool(
    name="invite_editor",
    title="Invite editor",
    access="write",
    confirm=True,
    description="Invite someone by email to edit a board and the boards inside it.",
    details=(
        "Adds the address as an editor, as Share, Invite editors via email does, and Milanote emails them a "
        "link. status is invited when they have no Milanote account yet (a free one is enough to edit), "
        "active when they do. Milanote allows inviting only once your account's email is verified; the "
        "free plan limits how many boards you can share. Remove them in the Share dialog to undo it. By "
        "default you confirm each call; you can switch that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /boards/{board_id}/editors",
    example_response=EXAMPLE_RESPONSE,
)
async def invite_editor(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    email = str(args.get("email") or "").strip().lower()
    if not _EMAIL.match(email):
        raise ToolError("email must be one email address.", ErrorCode.INVALID_INPUT)
    user = await me(ctx)
    if (user.get("email") or "").lower() == email:
        raise ToolError("That is this account's own address.", ErrorCode.INVALID_INPUT)
    if not user.get("emailVerifiedDate"):
        raise ToolError(
            "Milanote asks to verify this account's email before inviting. Open the link from Milanote's "
            "verification mail, then try again.",
            ErrorCode.TARGET_ERROR,
        )
    await board(ctx, bid)
    body = {
        "addUserIds": [],
        "updateUserIds": [],
        "removeUserIds": [],
        "addNewUserEmails": [email],
        "locale": LOCALE,
        "permissions": EDITOR,
    }
    answer = await call(ctx, "PUT", f"/api/elements/{bid}/permissions-invite", body=body)
    ids = [uid for uid in (answer.get("element") or {}).get("acl") or {} if uid != user["_id"]]
    users = (await call(ctx, "GET", "/api/users", params={"ids": ",".join(ids)})).get("users") or {} if ids else {}
    found = next(((uid, u) for uid, u in users.items() if (u.get("email") or "").lower() == email), (None, {}))
    status = "active" if found[1].get("status") == "ACTIVE" else "invited"
    return {
        "board_id": bid,
        "invited": email,
        "user_id": found[0],
        "role": "editor",
        "status": status,
        "board_url": board_url(bid),
    }
