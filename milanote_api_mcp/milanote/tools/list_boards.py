"""List boards."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.helpers import limit
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board, board_id, board_url, children, me, section

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "parent_board_id": {
            "type": "string",
            "description": "Only boards inside this board (ID or board URL). Default: the boards on your Home.",
        },
        "limit": {"type": "integer", "description": "1 to 200. Default: 50."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "parent_board_id": "1XiqvH1OOLn08n",
    "boards": [
        {
            "id": "1XiqwC1Mir4d4N",
            "title": "Brand refresh",
            "parent_board_id": "1XiqvH1OOLn08n",
            "section": "canvas",
            "url": "https://app.milanote.com/1XiqwC1Mir4d4N",
        },
        {
            "id": "1XiqZb1scDec7f",
            "title": "Novel outline",
            "parent_board_id": "1XiqvH1OOLn08n",
            "section": "unsorted",
            "url": "https://app.milanote.com/1XiqZb1scDec7f",
        },
    ],
    "has_more": False,
}


@tool(
    name="list_boards",
    title="List boards",
    access="read",
    confirm=False,
    description="Boards inside one board, by default the boards on your Home, with title, ID and link.",
    details=(
        "Lists the boards one level down: on your Home, or inside parent_board_id. Boards nest like folders, "
        "so pass a board's id as parent_board_id to walk down. Order is the board's own: the canvas top to "
        "bottom, then Unsorted. parent_board_id in the answer is the Home board's id when you left it out. "
        "Boards in the trash are left out."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /boards",
    example_response=EXAMPLE_RESPONSE,
)
async def list_boards(ctx: ToolContext, args: dict[str, Any]) -> Any:

    if args.get("parent_board_id"):
        parent = board_id(args["parent_board_id"], "parent_board_id")
    else:
        parent = (await me(ctx))["rootBoardId"]
    wanted = limit(args, 50, 200)
    found = [e for e in children(await board(ctx, parent), parent) if e.get("elementType") == "BOARD"]
    boards = [
        {
            "id": element["_id"],
            "title": (element.get("content") or {}).get("title") or "",
            "parent_board_id": parent,
            "section": section(element),
            "url": board_url(element["_id"]),
        }
        for element in found[:wanted]
    ]
    return {"parent_board_id": parent, "boards": boards, "has_more": len(found) > wanted}
