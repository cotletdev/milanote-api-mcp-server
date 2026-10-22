"""Get usage."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import call, card_type

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "additionalProperties": False}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "used": 9,
    "limit": 100,
    "unlimited": False,
    "exceeded": False,
    "by_type": {"note": 5, "board": 4, "todo_list": 3, "column": 2, "link": 1, "line": 1, "comment_thread": 5},
}


@tool(
    name="get_usage",
    title="Get usage",
    access="read",
    confirm=False,
    description="How many cards your account uses against the free plan's limit, by card type.",
    details=(
        "used is what Milanote counts toward the free plan's limit (100 cards, more with referral bonuses); "
        "once exceeded is true Milanote refuses new cards until you delete some or upgrade. On a paid plan "
        "unlimited is true and limit is null. by_type counts each kind of element you made, comments and "
        "lines included; Milanote decides which of them count toward used."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /usage",
    example_response=EXAMPLE_RESPONSE,
)
async def get_usage(ctx: ToolContext, _args: dict[str, Any]) -> Any:

    answer = await call(ctx, "GET", "/api/users/me/counts")
    unlimited = bool(answer.get("isUnlimited"))
    cap = answer.get("contentLimit") or {}
    counts = answer.get("counts") or {}
    return {
        "used": answer.get("totalUsage") or 0,
        "limit": None if unlimited else cap.get("current"),
        "unlimited": unlimited,
        "exceeded": bool(cap.get("exceeded")),
        "by_type": {card_type({"elementType": kind}): n for kind, n in counts.items()},
    }
