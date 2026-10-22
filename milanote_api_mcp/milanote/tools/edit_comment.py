"""Edit comment."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board, board_id, board_url, doc, me, sync

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "comment_id": {"type": "string", "description": "comment_id from get_board (include_comments) or add_comment."},
        "text": {"type": "string", "description": "New comment text, plain."},
    },
    "required": ["board_id", "comment_id", "text"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "comment_id": "cm_1Xite61Mitsmc9",
    "thread_id": "1Xitdk1Mitsmc8",
    "board_id": "1XiqwC1Mir4d4N",
    "text": "Check tide times first and parking.",
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


async def own_comment(ctx: ToolContext, bid: str, comment_id: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """The comment on this board, if this account wrote it (Milanote lets only the author change it)."""
    found = ((await board(ctx, bid)).get("comments") or {}).get(str(comment_id or "").strip())
    if not found:
        raise ToolError("comment_id is not a comment on this board.", ErrorCode.INVALID_INPUT)
    user = await me(ctx)
    if found.get("userId") != user["_id"]:
        raise ToolError("Only the author can change this comment.", ErrorCode.INVALID_INPUT)
    return user, found


@tool(
    name="edit_comment",
    title="Edit comment",
    access="write",
    confirm=False,
    description="Replace the text of a comment you wrote.",
    details=(
        "Overwrites your own comment with plain text, as Edit then Save does in the thread. Others' comments "
        "cannot be changed. People who already read it get no new notification."
    ),
    input_schema=INPUT_SCHEMA,
    route="PATCH /boards/{board_id}/comments/{comment_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def edit_comment(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    text = str(args.get("text") or "")
    if not text.strip():
        raise ToolError("text must not be empty.", ErrorCode.INVALID_INPUT)
    user, found = await own_comment(ctx, bid, args.get("comment_id"))
    _, link = await sync(ctx)
    action = {
        "_id": found["_id"],
        "elementId": found.get("elementId") or found.get("threadId"),
        "type": "COMMENTS_UPDATE",
        "text": doc(text),
        "userId": user["_id"],
        "activity": {"track": False, "boardId": bid},
    }
    await link.send(action, [bid])
    await link.close()
    return {
        "comment_id": found["_id"],
        "thread_id": found.get("threadId"),
        "board_id": bid,
        "text": text,
        "board_url": board_url(bid),
    }
