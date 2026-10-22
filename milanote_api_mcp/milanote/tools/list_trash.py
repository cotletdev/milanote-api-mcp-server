"""List trash."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.cards import card
from milanote_api_mcp.milanote.client import call, iso

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "additionalProperties": False}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "cards": [
        {
            "id": "1Xit9D1Y0ZjyeS",
            "type": "note",
            "section": "canvas",
            "text": "Golden hour at the pier, bring the 85mm.",
            "updated_at": "2026-10-18T17:46:44+02:00",
            "board_id": "1XiqwC1Mir4d4N",
            "trashed_at": "2026-10-18T17:53:24+02:00",
        }
    ],
    "has_more": False,
}


@tool(
    name="list_trash",
    title="List trash",
    access="read",
    confirm=False,
    description="Cards and boards you moved to the trash, with the board each one came from.",
    details=(
        "Lists your own trash, newest first: one entry per trashed card or board with its ID, content and "
        "board_id of the board it was on. restore_card puts one back where it was. Milanote keeps trashed "
        "items until you empty the trash in the app; has_more is true when it holds more than one page."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /trash",
    example_response=EXAMPLE_RESPONSE,
)
async def list_trash(ctx: ToolContext, _args: dict[str, Any]) -> Any:

    tz = ctx.profile.timezone
    answer = await call(ctx, "GET", "/api/users/me/trash", params={"other-users": "false"})
    rows = []
    for element in (answer.get("elements") or {}).values():
        location = element.get("location") or {}
        bid = str(location.get("parentId") or "").removesuffix("-trash")
        restore = (location.get("position") or {}).get("restoreLocation") or {}
        out = card({**element, "location": restore}, bid, tz)
        out.pop("column_id", None)
        out["board_id"] = bid
        out["trashed_at"] = iso((location.get("position") or {}).get("addedDate"), tz)
        rows.append(out)
    rows.sort(key=lambda row: row["trashed_at"] or "", reverse=True)
    return {"cards": rows, "has_more": bool(answer.get("hasMore"))}
