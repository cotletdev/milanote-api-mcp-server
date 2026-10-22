"""Add link."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import LOCALE, board, board_id, board_url, call, doc, sync, unsorted

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "url": {"type": "string", "description": "Web address to save, starting with http:// or https://."},
    },
    "required": ["board_id", "url"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "card_id": "1XiqzF1scDecar",
    "board_id": "1XiqwC1Mir4d4N",
    "type": "link",
    "url": "https://example.com/type-specimen",
    "title": "Type specimen",
    "description": "Free type specimen for the campaign headlines.",
    "board_url": "https://app.milanote.com/1XiqwC1Mir4d4N",
}


@tool(
    name="add_link",
    title="Add link",
    access="write",
    confirm=False,
    description="Link card for a web address, with the page's title and preview, added to Unsorted.",
    details=(
        "Adds one link card on top of the board's Unsorted panel. Milanote fetches the page itself and fills in "
        "the title, description and preview image, as when you paste a link; the answer returns what it found "
        "(title is null when the page gave none). On the free plan a link counts toward the 100 cards limit. "
        "Nobody is notified; move the card to the trash in Milanote to undo it."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /boards/{board_id}/links",
    example_response=EXAMPLE_RESPONSE,
)
async def add_link(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    url = str(args.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        raise ToolError("url must start with http:// or https://.", ErrorCode.INVALID_INPUT)
    location = unsorted(await board(ctx, bid), bid)
    user, link = await sync(ctx)
    card_id = link.new_id()
    # The preview comes first and the card only after it, so a link Milanote cannot read leaves no card.
    body = {"url": url, "elementId": card_id, "environmentFolder": "p", "userId": user["_id"], "locale": LOCALE}
    preview = await call(ctx, "POST", "/media-service/api/link", body=body)
    await link.create(card_id, "LINK", location, {"url": None})
    page = preview.get("link") or {"url": url}
    changes: dict[str, Any] = {
        "image": preview.get("image") or {},
        "mediaType": preview.get("mediaType") or "NO_MEDIA",
        "link": page,
        "provider": preview.get("provider") or {},
    }
    if preview.get("description"):
        changes.update(caption=doc(preview["description"]), showCaption=True)
    action = {
        "type": "ELEMENT_SET_TYPE",
        "id": card_id,
        "elementType": preview.get("elementType") or "LINK",
        "changes": changes,
        "timestamp": int(time.time() * 1000),
        "activity": {"track": False, "boardId": bid},
    }
    await link.send(action, [bid])
    await link.close()
    return {
        "card_id": card_id,
        "board_id": bid,
        "type": "link",
        "url": page.get("url") or url,
        "title": page.get("title"),
        "description": preview.get("description"),
        "board_url": board_url(bid),
    }
