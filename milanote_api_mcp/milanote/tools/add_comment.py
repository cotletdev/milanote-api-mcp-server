"""Add comment."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board, board_id, board_url, children, doc, sync, unsorted

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "text": {"type": "string", "description": "Comment text, plain."},
        "reply_to_id": {
            "type": "string",
            "description": "A comment thread ID or comment ID from get_board (include_comments) to reply in. "
            "Default: a new comment card.",
        },
    },
    "required": ["board_id", "text"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "comment_id": "cm_1XiqCw1scDecau",
    "thread_id": "1XiqCu1scDecat",
    "board_id": "1XiqwC1Mir4d4N",
    "text": "The new palette is on this board.",
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


def _thread(answer: dict[str, Any], bid: str, reply_to: str) -> str:
    threads = {e["_id"] for e in children(answer, bid) if e.get("elementType") == "COMMENT_THREAD"}
    if reply_to in threads:
        return reply_to
    comment = (answer.get("comments") or {}).get(reply_to) or {}
    if comment.get("threadId") in threads:
        return comment["threadId"]
    raise ToolError("reply_to_id is not a comment thread or comment on this board.", ErrorCode.INVALID_INPUT)


@tool(
    name="add_comment",
    title="Add comment",
    access="write",
    confirm=True,
    description="Comment card on a board, or a reply in a comment thread, posted under your name.",
    details=(
        "Without reply_to_id it adds a new comment card on top of the board's Unsorted panel; with it the "
        "comment joins that thread. Everyone who can open the board sees it under your name, and Milanote "
        "notifies people already in the thread. The text is plain: an @name stays text and tags nobody. "
        "Only you can edit or delete it afterwards, in Milanote. By default you confirm each call; you can "
        "switch that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /boards/{board_id}/comments",
    example_response=EXAMPLE_RESPONSE,
)
async def add_comment(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    text = str(args.get("text") or "")
    if not text.strip():
        raise ToolError("text must not be empty.", ErrorCode.INVALID_INPUT)
    answer = await board(ctx, bid)
    thread = _thread(answer, bid, str(args["reply_to_id"]).strip()) if args.get("reply_to_id") else None
    user, link = await sync(ctx)
    if thread is None:
        thread = link.new_id()
        await link.create(thread, "COMMENT_THREAD", unsorted(answer, bid), {"threadId": thread})
    comment_id = f"cm_{link.new_id()}"
    action = {
        "_id": comment_id,
        "type": "COMMENTS_ADD",
        "createdAt": int(time.time() * 1000),
        "userId": user["_id"],
        "elementId": thread,
        "threadId": thread,
        "text": doc(text),
        "activity": {"track": False, "boardId": bid},
    }
    await link.send(action, [bid])
    await link.close()
    return {"comment_id": comment_id, "thread_id": thread, "board_id": bid, "text": text, "board_url": board_url(bid)}
