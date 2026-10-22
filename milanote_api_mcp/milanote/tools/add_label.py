"""Add label."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import board, board_id, board_url, call, element, sync

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

# The colour Milanote gave the first label made from a card's Labels tool (18.10.2026).
_NEW_COLOR = "#ac2c75"

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "card_id": {"type": "string", "description": "Card ID from get_board."},
        "label": {"type": "string", "description": "Label name; a name you have not used yet creates the label."},
    },
    "required": ["board_id", "card_id", "label"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "card_id": "1XitgM1Mitsmcb",
    "board_id": "1XiqwC1Mir4d4N",
    "label_id": "lbl_1Xitha0000014s",
    "label": "Location",
    "created": False,
    "labels": ["lbl_1Xitha0000014s"],
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


@tool(
    name="add_label",
    title="Add label",
    access="write",
    confirm=False,
    description="Put a label on a card, creating the label when the name is new.",
    details=(
        "Matches the name against your labels (list_labels) without regard to case; created is true when it "
        "made a new one. The card keeps its other labels. Editors of the board see the label on the card."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /boards/{board_id}/cards/{card_id}/labels",
    example_response=EXAMPLE_RESPONSE,
)
async def add_label(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    name = str(args.get("label") or "").strip()
    if not name:
        raise ToolError("label must not be empty.", ErrorCode.INVALID_INPUT)
    found = element(await board(ctx, bid), bid, args.get("card_id"))
    labels = (await call(ctx, "GET", "/api/labels")).get("labels") or []
    existing = next((row for row in labels if (row.get("name") or "").lower() == name.lower()), None)
    user, link = await sync(ctx)
    now = int(time.time() * 1000)
    if existing:
        label_id, name = existing["_id"], existing.get("name") or name
    else:
        label_id = f"lbl_{link.new_id()}"
        meta = {"creator": user["_id"], "createdTime": now, "modifiedTime": now}
        label = {"_id": label_id, "name": name, "color": _NEW_COLOR, "meta": meta}
        await link.send({"type": "LABEL_CREATE", "label": label}, [f"{user['_id']}-PERSONAL"])
    current = list((found.get("content") or {}).get("labels") or [])
    if label_id not in current:
        action = {
            "type": "ELEMENT_UPDATE",
            "updateType": "LABEL",
            "updates": [
                {"id": found["_id"], "changes": {"labels": [*current, label_id]}, "meta": {"addedLabelIds": [label_id]}}
            ],
            "timestamp": now,
            "recalculateChannels": False,
            "activity": {"track": False, "boardId": bid},
        }
        await link.send(action, [bid])
        current.append(label_id)
    await link.close()
    return {
        "card_id": found["_id"],
        "board_id": bid,
        "label_id": label_id,
        "label": name,
        "created": existing is None,
        "labels": current,
        "board_url": board_url(bid),
    }
