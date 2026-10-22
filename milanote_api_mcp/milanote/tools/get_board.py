"""Get board."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.cards import card, comments
from milanote_api_mcp.milanote.client import board, board_id, board_url, call, children

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "include_comments": {
            "type": "boolean",
            "description": "Also return comment threads with their comments. Default: false.",
        },
    },
    "required": ["board_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "board_id": "1XiqwC1Mir4d4N",
    "title": "Q1 campaign",
    "url": "https://app.milanote.com/1XiqwC1Mir4d4N",
    "cards": [
        {
            "id": "1Xiqxr1scDecaq",
            "type": "note",
            "section": "canvas",
            "text": "Palette: warm greys with one orange accent.",
            "updated_at": "2026-10-18T15:03:00+02:00",
        },
        {
            "id": "1XiqzF1scDecar",
            "type": "link",
            "section": "canvas",
            "url": "https://example.com/type-specimen",
            "title": "Type specimen",
            "description": "Free type specimen for the campaign headlines.",
            "updated_at": "2026-10-18T15:05:18+02:00",
        },
        {
            "id": "1XiqzZ1scDecas",
            "type": "todo_list",
            "section": "canvas",
            "title": None,
            "tasks": [
                {"task_id": "task-UyDA675rUgS8q", "text": "Shorten the intro", "done": False, "due_date": "2026-10-25"},
                {
                    "task_id": "task-gwg6np5EiQiyU",
                    "text": "Swap the hero image",
                    "done": True,
                    "due_date": "2026-10-21",
                    "due_time": "14:30",
                },
            ],
            "updated_at": "2026-10-18T15:06:30+02:00",
        },
        {
            "id": "1XiqIw1OOLy10T",
            "type": "image",
            "section": "unsorted",
            "file_name": "location-01.png",
            "image_url": "https://app.milanote.com/media/p/images/1XiqIw1OOLy10T/ERR/location-01.png",
            "width": 1200,
            "height": 800,
            "updated_at": "2026-10-18T15:14:27+02:00",
        },
        {
            "id": "1XiqC51scDec9a",
            "type": "board",
            "section": "canvas",
            "title": "Social assets",
            "board_id": "1XiqC51scDec9a",
            "url": "https://app.milanote.com/1XiqC51scDec9a",
            "updated_at": "2026-10-18T15:02:09+02:00",
        },
    ],
}


@tool(
    name="get_board",
    title="Get board",
    access="read",
    confirm=False,
    description="Every card on a board: notes, links, images, files, to-do lists, columns and sub-boards.",
    details=(
        "Returns one entry per card with its type, ID and content, so other tools can point at it. Order is the "
        "board's: the canvas top to bottom, then the Unsorted panel (section says which). Notes come back as "
        "plain text. To-do lists list each task with its done state and due date (due_time only when one was "
        "set). Cards inside a column carry column_id; color and labels (by name) appear when a card has them. "
        "Sub-boards appear as cards with their own board_id; call get_board again to open one. Drawings, "
        "lines and tables come back with their type and ID only. "
        "include_comments adds comment threads with author, text and time."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /boards/{board_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_board(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    tz = ctx.profile.timezone
    answer = await board(ctx, bid)
    rows = children(answer, bid)
    if not args.get("include_comments"):
        rows = [e for e in rows if e.get("elementType") != "COMMENT_THREAD"]
    cards = [card(element, bid, tz) for element in rows]
    names = {key: row.get("name") or "" for key, row in (answer.get("labels") or {}).items()}
    for one in cards:
        if one.get("labels"):
            one["labels"] = [names.get(label, label) for label in one["labels"]]
    threads = [c for c in cards if c["type"] == "comment_thread"]
    if threads:
        authors = {c.get("userId") for c in (answer.get("comments") or {}).values() if c.get("userId")}
        names = await _names(ctx, sorted(authors))
        for thread in threads:
            thread["comments"] = comments(answer, thread["id"], names, tz)
    title = ((answer["elements"][bid]).get("content") or {}).get("title") or ""
    return {"board_id": bid, "title": title, "url": board_url(bid), "cards": cards}


async def _names(ctx: ToolContext, user_ids: list[str]) -> dict[str, str]:
    if not user_ids:
        return {}
    users = (await call(ctx, "GET", "/api/users", params={"ids": ",".join(user_ids)})).get("users") or {}
    return {uid: ((user.get("name") or {}).get("displayName") or "Unknown") for uid, user in users.items()}
