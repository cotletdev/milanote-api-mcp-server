"""Add to-do list."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board, board_id, board_url, sync, task_id, unsorted

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

MAX_TASKS = 50
# What Milanote's due date picker stores (18.10.2026): a date alone means 5 PM that day, and the default
# reminder is 9 AM the day it's due, both in the user's time zone.
_DATE_ONLY_AT = time(17, 0)
_REMINDER_AT = time(9, 0)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "title": {"type": "string", "description": "List title. Default: no title."},
        "tasks": {
            "type": "array",
            "description": f"1 to {MAX_TASKS} tasks, in order.",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Task text."},
                    "due_date": {"type": "string", "description": "YYYY-MM-DD. Default: no due date."},
                    "due_time": {"type": "string", "description": "HH:MM, 24-hour, with due_date."},
                },
                "required": ["text"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["board_id", "tasks"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "card_id": "1XiqzZ1scDecas",
    "board_id": "1XiqwC1Mir4d4N",
    "title": "Call edits",
    "tasks": [
        {"task_id": "task-UyDA675rUgS8q", "text": "Shorten the intro", "done": False, "due_date": "2026-10-25"},
        {
            "task_id": "task-gwg6np5EiQiyU",
            "text": "Swap the hero image",
            "done": False,
            "due_date": "2026-10-21",
            "due_time": "14:30",
        },
    ],
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


def _due(task: dict[str, Any], tz: str) -> dict[str, Any] | None:
    if not task.get("due_date"):
        if task.get("due_time"):
            raise ToolError("due_time needs a due_date.", ErrorCode.INVALID_INPUT)
        return None
    try:
        day = date.fromisoformat(str(task["due_date"]))
        at = time.fromisoformat(str(task["due_time"])) if task.get("due_time") else _DATE_ONLY_AT
    except ValueError as exc:
        raise ToolError("due_date must be YYYY-MM-DD and due_time HH:MM.", ErrorCode.INVALID_INPUT) from exc
    zone = ZoneInfo(tz)
    due = datetime.combine(day, at, zone)
    reminder = datetime.combine(day, _REMINDER_AT, zone)
    return {
        "timestamp": int(due.timestamp() * 1000),
        "hasTime": bool(task.get("due_time")),
        "reminder": "9am",
        "reminderTimestamp": int(reminder.timestamp() * 1000),
    }


def _item(task: dict[str, Any], tz: str) -> tuple[dict[str, Any], dict[str, Any]]:
    text = str(task.get("text") or "").strip()
    if not text:
        raise ToolError("Every task needs text.", ErrorCode.INVALID_INPUT)
    due = _due(task, tz)
    tid = task_id()
    node = {
        "type": "taskItem",
        "attrs": {
            "taskId": tid,
            "checked": False,
            "dueDate": due,
            "assignments": [],
            "labels": [],
            "reactions": [],
            "showAssignments": False,
            "showDueDate": due is not None,
        },
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }
    out: dict[str, Any] = {"task_id": tid, "text": text, "done": False, "due_date": task.get("due_date")}
    if task.get("due_time"):
        out["due_time"] = task["due_time"]
    return node, out


@tool(
    name="add_todo_list",
    title="Add to-do list",
    access="write",
    confirm=False,
    description="To-do list card with tasks, each with an optional due date and time, added to Unsorted.",
    details=(
        "Creates one to-do list on top of the board's Unsorted panel with all its tasks, unchecked, and returns "
        "each task_id. A due date without a time is due at 5 PM; Milanote reminds you at 9 AM the day it's "
        "due, by the channels in your notification settings. Times are in the Cloud Browser's time zone. "
        "Nobody else is notified; move the list to the trash in Milanote to undo it."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /boards/{board_id}/todo-lists",
    example_response=EXAMPLE_RESPONSE,
)
async def add_todo_list(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    tasks = args.get("tasks")
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= MAX_TASKS:
        raise ToolError(f"tasks must be a list of 1 to {MAX_TASKS} tasks.", ErrorCode.INVALID_INPUT)
    items = [_item(task if isinstance(task, dict) else {"text": task}, ctx.profile.timezone) for task in tasks]
    title = str(args.get("title") or "").strip() or None
    # The title is the document's first node, as the list's Title tool writes it (18.10.2026).
    heading = [{"type": "taskListTitle", "content": [{"type": "text", "text": title}]}] if title else []
    content = {
        "title": None,
        "showTitle": False,
        "version": "V2",
        "textContent": {
            "type": "doc",
            "attrs": {"hiddenTaskListTitle": None},
            "content": [*heading, {"type": "taskList", "content": [node for node, _ in items]}],
        },
    }
    location = unsorted(await board(ctx, bid), bid)
    _, link = await sync(ctx)
    card_id = link.new_id()
    await link.create(card_id, "TASK_LIST", location, content)
    await link.close()
    return {
        "card_id": card_id,
        "board_id": bid,
        "title": title,
        "tasks": [out for _, out in items],
        "board_url": board_url(bid),
    }
