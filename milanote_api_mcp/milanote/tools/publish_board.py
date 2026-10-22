"""Publish board."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import LOCALE, board, board_id, board_url, call, public_link, update

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "allow_comments": {
            "type": "boolean",
            "description": "Let viewers of the link comment, react and draw. Default false.",
        },
        "allow_downloads": {
            "type": "boolean",
            "description": "Show download links on files to viewers. Default true.",
        },
    },
    "required": ["board_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "board_id": "1XiqwC1Mir4d4N",
    "read_only_link": "https://app.milanote.com/1XiqwC1Mir4d4N?p=7xo857HjFby",
    "allow_comments": False,
    "allow_downloads": True,
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


@tool(
    name="publish_board",
    title="Publish board",
    access="write",
    confirm=True,
    description="Turn on a board's read-only link, which anyone can open without signing up.",
    details=(
        "Does what Share, Enable read-only link does and returns the link. Anyone who has it sees the board "
        "and the boards inside it, without a Milanote account. A board keeps one link: publishing again, even "
        "after unpublish_board, brings back the same link with these settings. unpublish_board turns it off. "
        "By default you confirm each call; you can switch that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /boards/{board_id}/publish",
    example_response=EXAMPLE_RESPONSE,
)
async def publish_board(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    comments = bool(args.get("allow_comments", False))
    downloads = bool(args.get("allow_downloads", True))
    content = (await board(ctx, bid))["elements"][bid].get("content") or {}
    body = {
        "addUserIds": [],
        "addNewUserEmails": [],
        "updateUserIds": [],
        "removeUserIds": [],
        "locale": LOCALE,
        "commentsEnabled": comments,
    }
    await call(ctx, "PUT", f"/api/elements/{bid}/publish", body=body)
    if bool(content.get("publishedMediaDownloadDisabled")) == downloads:
        await update(ctx, bid, bid, {"publishedMediaDownloadDisabled": not downloads})
    link = await public_link(ctx, bid)
    if not link:
        raise ToolError("Milanote did not turn the read-only link on.", ErrorCode.TARGET_ERROR)
    return {
        "board_id": bid,
        "read_only_link": link,
        "allow_comments": comments,
        "allow_downloads": downloads,
        "board_url": board_url(bid),
    }
