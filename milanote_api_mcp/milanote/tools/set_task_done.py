"""Set task done."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.cards import tasks
from milanote_api_mcp.milanote.client import board, board_id, board_url, element, plain, update

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "card_id": {"type": "string", "description": "To-do list ID from get_board."},
        "task": {"type": "string", "description": "The task's task_id from get_board, or its exact text."},
        "done": {"type": "boolean", "description": "true ticks it, false unticks it. Default true."},
    },
    "required": ["board_id", "card_id", "task"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "card_id": "1Xitbu1Mitsmc7",
    "board_id": "1XiqwC1Mir4d4N",
    "tasks": [
        {"task_id": "task-n18Bt6Fm86Quu", "text": "Batteries", "done": True, "due_date": None},
        {"task_id": "task-JPS6v0qaWeG82", "text": "Reflector", "done": False, "due_date": None},
    ],
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


def _tick(node: Any, wanted: str, done: bool) -> int:
    """Sets checked on the task whose id or text matches; returns how many matched."""
    if not isinstance(node, dict):
        return 0
    if node.get("type") == "taskItem":
        attrs = node.setdefault("attrs", {})
        text = plain({"type": "doc", "content": node.get("content") or []}).strip()
        if wanted in (attrs.get("taskId"), text):
            attrs["checked"] = done
            return 1
        return 0
    return sum(_tick(child, wanted, done) for child in node.get("content") or [])


@tool(
    name="set_task_done",
    title="Set task done",
    access="write",
    confirm=False,
    description="Tick or untick one task in a to-do list.",
    details=(
        "Finds the task by task_id or by its exact text and sets it done or not done, as clicking its "
        "checkbox does; the rest of the list stays as it was. Returns the whole list after the change. When "
        "two tasks share the text, pass the task_id instead."
    ),
    input_schema=INPUT_SCHEMA,
    route="PUT /boards/{board_id}/cards/{card_id}/tasks/{task}/done",
    example_response=EXAMPLE_RESPONSE,
)
async def set_task_done(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    wanted = str(args.get("task") or "").strip()
    if not wanted:
        raise ToolError("task must not be empty.", ErrorCode.INVALID_INPUT)
    found = element(await board(ctx, bid), bid, args.get("card_id"))
    if found.get("elementType") != "TASK_LIST":
        raise ToolError("card_id is not a to-do list.", ErrorCode.INVALID_INPUT)
    content = copy.deepcopy(found.get("content") or {})
    matched = _tick(content.get("textContent"), wanted, bool(args.get("done", True)))
    if matched == 0:
        raise ToolError("No task in this list has that task_id or text.", ErrorCode.INVALID_INPUT)
    if matched > 1:
        raise ToolError("Several tasks have that text; pass the task_id.", ErrorCode.INVALID_INPUT)
    await update(ctx, bid, found["_id"], {"textContent": content["textContent"]})
    return {
        "card_id": found["_id"],
        "board_id": bid,
        "tasks": tasks(content, ctx.profile.timezone),
        "board_url": board_url(bid),
    }
