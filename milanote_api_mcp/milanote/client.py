"""Milanote web requests recorded on a team test account (18.10.2026).

Reads are REST on app.milanote.com/api with the account's session cookie: the user (`/api/users/me`), a board
with every element inside it (`/api/boards?ids=`), search, export and sharing. Writes go through `sync.Sync`.
A board's cards are elements whose `location.parentId` is the board (or one of its columns); `section` says
where they sit: CANVAS, INBOX (the "Unsorted" panel) or TRASH. Cards the tools add land in Unsorted, where
Milanote itself puts uploads and cards added from outside, so they never cover cards on the canvas.
Ids stay Milanote's strings; times are ISO 8601 in the Cloud Browser's time zone.
"""

from __future__ import annotations

import re
import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.milanote.sync import APP, Sync

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

LOCALE = "en-au"
# Base62 seconds, a 6-character client id and a counter: 13 to 16 characters.
_ID = re.compile(r"\b([0-9A-Za-z]{13,16})\b")
_CARD_TYPES = {
    "CARD": "note",
    "LINK": "link",
    "IMAGE": "image",
    "FILE": "file",
    "TASK_LIST": "todo_list",
    "BOARD": "board",
    "COLUMN": "column",
    "COMMENT_THREAD": "comment_thread",
}
# Colours Milanote gave a board created from the toolbar (18.10.2026); a board needs a palette for its cards.
_PALETTE = ["#8bafba", "#a1c8cb", "#82cec7", "#a1dbd0", "#f5ceaa", "#e2aca8", "#f07167"]


async def call(
    ctx: ToolContext, method: str, path: str, *, params: dict[str, Any] | None = None, body: Any = None
) -> Any:
    """One Milanote API request; errors become messages for the agent."""
    url = path if path.startswith("https://") else f"{APP}{path}"
    headers = {"accept": "application/json", "referer": f"{APP}/", "origin": APP}
    response = await ctx.call(method, url, params=params, json=body, headers=headers)
    if response.status == 404:
        raise ToolError("Milanote has no such board, or this account cannot see it.", ErrorCode.TARGET_ERROR)
    if response.status == 429:
        raise ToolError("Milanote is limiting this account; try again in a few minutes.", ErrorCode.RATE_LIMITED)
    if response.status >= 400:
        message = _error_message(response)
        raise ToolError(message or f"Milanote refused the request ({response.status}).", ErrorCode.TARGET_ERROR)
    try:
        return response.json() if response.text.strip() else {}
    except ValueError as exc:
        raise ToolError("Milanote answered with a page instead of data.", ErrorCode.TARGET_ERROR) from exc


def _error_message(response: Any) -> str | None:
    try:
        error = (response.json() or {}).get("error") or {}
    except ValueError:
        return None
    return error.get("message") if isinstance(error, dict) else None


async def me(ctx: ToolContext) -> dict[str, Any]:
    """The signed-in user: ids of Home (`rootBoardId`), the fresh clientId for new elements. Never returned as is."""
    user = (await call(ctx, "GET", "/api/users/me")).get("user") or {}
    if not user.get("_id"):
        raise ToolError("Milanote did not say who is signed in.", ErrorCode.TARGET_ERROR)
    return user


async def sync(ctx: ToolContext) -> tuple[dict[str, Any], Sync]:
    user = await me(ctx)
    return user, await Sync(ctx, user).open()


def board_id(value: Any, field: str = "board_id") -> str:
    """A board id, or the id inside a board URL (app.milanote.com/1XiqwC1Mir4d4N/board-name)."""
    text = str(value or "").strip()
    found = _ID.search(text.split("milanote.com/")[-1])
    if not found:
        raise ToolError(f"{field} must be a board ID from list_boards or a board URL.", ErrorCode.INVALID_INPUT)
    return found.group(1)


def board_url(element_id: str) -> str:
    return f"{APP}/{element_id}"


async def board(ctx: ToolContext, bid: str) -> dict[str, Any]:
    """The board and every element in it, with its comments: Milanote's own board load."""
    answer = await call(
        ctx, "GET", "/api/boards", params={"excludeSelf": "false", "loadAncestors": "false", "ids": bid}
    )
    elements = answer.get("elements") or {}
    found = elements.get(bid)
    if not found or found.get("elementType") != "BOARD":
        raise ToolError("Milanote has no such board, or this account cannot see it.", ErrorCode.TARGET_ERROR)
    return answer


def children(answer: dict[str, Any], bid: str) -> list[dict[str, Any]]:
    """Elements on the board itself or inside its columns, without the trash; canvas first, in reading order."""
    elements = answer.get("elements") or {}
    columns = {
        e["_id"]
        for e in elements.values()
        if e.get("elementType") == "COLUMN"
        and (e.get("location") or {}).get("parentId") == bid
        and (e.get("location") or {}).get("section") != "TRASH"
    }
    rows = []
    for element in elements.values():
        location = element.get("location") or {}
        parent, section = location.get("parentId"), location.get("section")
        if element["_id"] == bid or section == "TRASH":
            continue
        if parent == bid or (parent in columns and parent != element["_id"]):
            rows.append(element)
    return sorted(rows, key=_order)


def _order(element: dict[str, Any]) -> tuple[int, float, float]:
    location = element.get("location") or {}
    position = location.get("position") or {}
    if location.get("section") == "INBOX":
        return (1, float(position.get("score") or 0), 0.0)
    return (0, float(position.get("y") or 0), float(position.get("x") or 0))


def unsorted(answer: dict[str, Any], bid: str) -> dict[str, Any]:
    """Where a new card goes: on top of the board's Unsorted panel."""
    scores = [
        float(((e.get("location") or {}).get("position") or {}).get("score") or 0)
        for e in children(answer, bid)
        if (e.get("location") or {}).get("section") == "INBOX"
    ]
    return {"parentId": bid, "section": "INBOX", "position": {"index": 0, "score": min(scores, default=0) - 1}}


def card_type(element: dict[str, Any]) -> str:
    kind = element.get("elementType") or ""
    return _CARD_TYPES.get(kind, kind.lower())


def section(element: dict[str, Any]) -> str:
    return "unsorted" if (element.get("location") or {}).get("section") == "INBOX" else "canvas"


def doc(text: str) -> dict[str, Any]:
    """Plain text as Milanote's rich-text document: one paragraph per line."""
    paragraphs = [
        {"type": "paragraph", "content": [{"type": "text", "text": line}]} if line else {"type": "paragraph"}
        for line in str(text).split("\n")
    ]
    return {"type": "doc", "content": paragraphs}


def plain(node: Any) -> str:
    """The text of a rich-text document, paragraphs and list items on their own lines."""
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return ""
    if node.get("type") == "text":
        return node.get("text") or ""
    inner = [plain(child) for child in node.get("content") or []]
    joiner = "\n" if node.get("type") in ("doc", "bulletList", "orderedList", "taskList", "listItem") else ""
    return joiner.join(part for part in inner if part is not None).strip("\n")


def task_id() -> str:
    """The id Milanote's editor gives a task, e.g. task-UyDA675rUgS8q."""
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "task-" + "".join(secrets.choice(alphabet) for _ in range(13))


def board_content(title: str) -> dict[str, Any]:
    return {"title": title, "icon": None, "color": None, "secondaryColor": None, "defaultColorPalette": _PALETTE}


def iso(ms: Any, tz: str) -> str | None:
    if not ms:
        return None
    return datetime.fromtimestamp(int(ms) / 1000, UTC).astimezone(ZoneInfo(tz)).isoformat(timespec="seconds")


async def trash(ctx: ToolContext, link: Sync, ids: list[str], answer: dict[str, Any]) -> None:
    """Moves elements to their board's trash, as the Delete key does (they stay restorable in Milanote)."""
    elements = answer.get("elements") or {}
    now = int(datetime.now(UTC).timestamp() * 1000)
    moves, channels = [], []
    for element_id in ids:
        location = (elements.get(element_id) or {}).get("location") or {}
        parent = location.get("parentId")
        if not parent:
            continue
        moves.append(
            {
                "id": element_id,
                "location": {
                    "parentId": f"{parent}-trash",
                    "section": "TRASH",
                    "position": {"addedDate": now, "restoreLocation": location},
                },
                "from": location,
            }
        )
        channels.append(parent)
    if moves:
        action = {
            "type": "ELEMENT_MOVE_MULTI",
            "moves": moves,
            "timestamp": now,
            "moveOperation": "TRASH",
            "monitoring": {"operation": "TRASH"},
            "activity": {"track": False},
        }
        await link.send(action, sorted(set(channels)))


def element(answer: dict[str, Any], bid: str, element_id: Any, field: str = "card_id") -> dict[str, Any]:
    """A card on the board (or in one of its columns), from a board load; the trash does not count."""
    wanted = str(element_id or "").strip()
    for found in children(answer, bid):
        if found["_id"] == wanted:
            return found
    raise ToolError(f"{field} is not a card on this board; get_board lists them.", ErrorCode.INVALID_INPUT)


async def move(link: Sync, moves: list[dict[str, Any]], operation: str = "DROP") -> None:
    """Moves elements the way drag and drop does: each move is {id, location, from}."""
    channels = set()
    for one in moves:
        for side in ("location", "from"):
            parent = str((one.get(side) or {}).get("parentId") or "")
            if parent:
                channels.add(parent.removesuffix("-trash"))
    action = {
        "type": "ELEMENT_MOVE_MULTI",
        "moves": moves,
        "timestamp": int(datetime.now(UTC).timestamp() * 1000),
        "moveOperation": operation,
        "monitoring": {"operation": operation},
        "activity": {"track": False},
    }
    await link.send(action, sorted(channels))


async def update(ctx: ToolContext, bid: str, element_id: str, changes: dict[str, Any]) -> None:
    """One ELEMENT_UPDATE on its own connection."""
    _, link = await sync(ctx)
    await link.update(element_id, bid, changes)
    await link.close()


# Milanote's permission bits on a board's acl (18.10.2026): 31 owner, 15 editor, 1 the read-only link.
OWNER, EDITOR = 31, 15


async def public_link(ctx: ToolContext, bid: str, slug: str = "") -> str | None:
    """The board's read-only link when it has one: the board URL with ?p= and the link's permission id."""
    rows = (await call(ctx, "GET", f"/api/permissions/board/{bid}")).get("permissions") or []
    active = next((r for r in rows if r.get("type") == "PUBLIC" and r.get("status") == "ACTIVE"), None)
    if not active:
        return None
    return f"{board_url(bid)}{'/' + slug if slug else ''}?p={active['_id']}"
