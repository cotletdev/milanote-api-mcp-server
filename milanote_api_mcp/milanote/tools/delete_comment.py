"""Delete comment."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board_id, board_url, sync
from milanote_api_mcp.milanote.tools.edit_comment import own_comment

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "comment_id": {"type": "string", "description": "comment_id from get_board (include_comments) or add_comment."},
    },
    "required": ["board_id", "comment_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "deleted": "cm_1Xite61Mitsmc9",
    "thread_id": "1Xitdk1Mitsmc8",
    "board_id": "1XiqwC1Mir4d4N",
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


@tool(
    name="delete_comment",
    title="Delete comment",
    access="write",
    confirm=True,
    description="Delete a comment you wrote, for everyone.",
    details=(
        "Removes your own comment from its thread; the thread and other people's comments stay. There is no "
        "trash for comments, so it cannot be brought back. By default you confirm each call; you can switch "
        "that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="DELETE /boards/{board_id}/comments/{comment_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def delete_comment(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    user, found = await own_comment(ctx, bid, args.get("comment_id"))
    _, link = await sync(ctx)
    action = {
        "_id": found["_id"],
        "elementId": found.get("elementId") or found.get("threadId"),
        "type": "COMMENTS_DELETE",
        "threadId": found.get("threadId"),
        "userId": user["_id"],
        "activity": {"track": False, "boardId": bid},
    }
    await link.send(action, [bid])
    await link.close()
    return {"deleted": found["_id"], "thread_id": found.get("threadId"), "board_id": bid, "board_url": board_url(bid)}
