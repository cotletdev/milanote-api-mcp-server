"""Get sharing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import EDITOR, OWNER, board, board_id, board_url, call, iso, public_link

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
    "people": [
        {"user_id": "6ad4caee4f8292b698c35385", "name": "Dana Reyes", "role": "owner", "status": "active"},
        {"user_id": "6ad4c6a152905d94d7495d08", "name": "Sam Lee", "role": "editor", "status": "invited"},
    ],
    "read_only_link": "https://app.milanote.com/1XiqwC1Mir4d4N?p=7xo857HjFby",
    "comments_on_link": False,
    "downloads_on_link": True,
    "last_edited_at": "2026-10-18T17:51:41+02:00",
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


@tool(
    name="get_sharing",
    title="Get sharing",
    access="read",
    confirm=False,
    description="Who can open a board: owner, editors and the read-only link with its settings.",
    details=(
        "Lists the board's owner and the editors invited to it; status is invited for someone who has not "
        "made a Milanote account yet. Editors of a parent board can open it too and are not listed here. "
        "read_only_link is null until publish_board turns the link on; comments_on_link and downloads_on_link "
        "say what viewers of that link may do."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /boards/{board_id}/sharing",
    example_response=EXAMPLE_RESPONSE,
)
async def get_sharing(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    found = (await board(ctx, bid))["elements"][bid]
    content = found.get("content") or {}
    owner = (found.get("meta") or {}).get("creator")
    editors = [uid for uid, bits in (found.get("acl") or {}).items() if bits in (OWNER, EDITOR) and uid != owner]
    ids = [uid for uid in [owner, *editors] if uid]
    users = (await call(ctx, "GET", "/api/users", params={"ids": ",".join(ids)})).get("users") or {} if ids else {}
    people = [
        {
            "user_id": uid,
            "name": ((users.get(uid) or {}).get("name") or {}).get("displayName") or None,
            "role": "owner" if uid == owner else "editor",
            "status": "active" if (users.get(uid) or {}).get("status") == "ACTIVE" else "invited",
        }
        for uid in ids
    ]
    link = await public_link(ctx, bid) if content.get("published") else None
    return {
        "board_id": bid,
        "people": people,
        "read_only_link": link,
        "comments_on_link": bool(link and content.get("publishedFeedbackEnabled")),
        "downloads_on_link": bool(link and not content.get("publishedMediaDownloadDisabled")),
        "last_edited_at": iso((found.get("meta") or {}).get("modifiedTime"), ctx.profile.timezone),
        "board_url": board_url(bid),
    }
