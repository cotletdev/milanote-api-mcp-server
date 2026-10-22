"""List labels."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import call

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "additionalProperties": False}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "labels": [{"label_id": "lbl_1Xitha0000014s", "name": "Location", "color": "#ac2c75"}]
}


@tool(
    name="list_labels",
    title="List labels",
    access="read",
    confirm=False,
    description="The labels you can put on cards, with name and colour.",
    details=(
        "Labels are yours, not a board's: the same label can sit on cards across all your boards. add_label "
        "puts one on a card by name and creates it when it is new."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /labels",
    example_response=EXAMPLE_RESPONSE,
)
async def list_labels(ctx: ToolContext, _args: dict[str, Any]) -> Any:

    labels = (await call(ctx, "GET", "/api/labels")).get("labels") or []
    return {
        "labels": [
            {"label_id": row["_id"], "name": row.get("name") or "", "color": row.get("color")}
            for row in labels
            if row.get("_id")
        ]
    }
