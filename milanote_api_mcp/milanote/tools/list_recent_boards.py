"""List recent boards."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.helpers import limit
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board_url, call, iso

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"limit": {"type": "integer", "description": "1 to 50. Default 20."}},
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "boards": [
        {
            "id": "1XiqwC1Mir4d4N",
            "title": "Spring shoot",
            "last_viewed_at": "2026-10-18T17:51:08+02:00",
            "views": 3,
            "url": "https://app.milanote.com/1XiqwC1Mir4d4N",
        }
    ]
}


@tool(
    name="list_recent_boards",
    title="List recent boards",
    access="read",
    confirm=False,
    description="Boards you opened lately, newest first, wherever they sit in your board tree.",
    details=(
        "The list behind Milanote's search box before you type: every board you viewed, shared ones too, "
        "with when you last opened it and how many times. Home and Quick notes appear like any other board. "
        "Boards you have not opened since they were made are missing; list_boards walks the tree instead."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /boards/recent",
    example_response=EXAMPLE_RESPONSE,
)
async def list_recent_boards(ctx: ToolContext, args: dict[str, Any]) -> Any:

    tz = ctx.profile.timezone
    answer = await call(ctx, "GET", "/api/users/me/history", params={"limit": limit(args, 20, 50)})
    elements = answer.get("elements") or {}
    boards = []
    for row in answer.get("history") or []:
        found = elements.get(row.get("elementId")) or {}
        if found.get("elementType") != "BOARD":
            continue
        boards.append(
            {
                "id": found["_id"],
                "title": (found.get("content") or {}).get("title") or "",
                "last_viewed_at": iso(row.get("lastView"), tz),
                "views": row.get("viewCount") or 0,
                "url": board_url(found["_id"]),
            }
        )
    return {"boards": boards}
