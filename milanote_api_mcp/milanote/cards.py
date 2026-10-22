"""Milanote elements as the cards get_board returns (shapes recorded 18.10.2026)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from milanote_api_mcp.milanote.client import board_url, card_type, iso, plain, section


def due(value: Any, tz: str) -> dict[str, Any]:
    """A task's due date: Milanote keeps one timestamp, 5 PM local when no time was set."""
    if not isinstance(value, dict) or not value.get("timestamp"):
        return {"due_date": None}
    when = datetime.fromtimestamp(int(value["timestamp"]) / 1000, UTC).astimezone(ZoneInfo(tz))
    out: dict[str, Any] = {"due_date": when.date().isoformat()}
    if value.get("hasTime"):
        out["due_time"] = when.strftime("%H:%M")
    return out


def tasks(content: dict[str, Any], tz: str) -> list[dict[str, Any]]:
    found = []

    def walk(node: Any) -> None:
        if not isinstance(node, dict):
            return
        if node.get("type") == "taskItem":
            attrs = node.get("attrs") or {}
            found.append(
                {
                    "task_id": attrs.get("taskId"),
                    "text": plain({"type": "doc", "content": node.get("content") or []}),
                    "done": bool(attrs.get("checked")),
                    **due(attrs.get("dueDate"), tz),
                }
            )
            return
        for child in node.get("content") or []:
            walk(child)

    walk(content.get("textContent"))
    return found


def _list_title(content: dict[str, Any]) -> str | None:
    """The Title tool writes a taskListTitle node first in the document; a shown content.title is the older way."""
    for node in (content.get("textContent") or {}).get("content") or []:
        if isinstance(node, dict) and node.get("type") == "taskListTitle":
            return plain(node) or None
    title = content.get("title") if content.get("showTitle") else None
    return (plain(title) if isinstance(title, dict) else title) or None


def card(element: dict[str, Any], bid: str, tz: str) -> dict[str, Any]:
    content = element.get("content") or {}
    kind = card_type(element)
    out: dict[str, Any] = {"id": element["_id"], "type": kind, "section": section(element)}
    parent = (element.get("location") or {}).get("parentId")
    if parent and parent != bid:
        out["column_id"] = parent
    if kind == "note":
        out["text"] = plain(content.get("textContent"))
    elif kind == "link":
        link = content.get("link") or {}
        out.update(url=link.get("url") or content.get("url"), title=link.get("title"))
        out["description"] = plain(content.get("caption")) or None
    elif kind == "image":
        image = content.get("image") or {}
        out.update(
            file_name=(content.get("file") or {}).get("filename"),
            image_url=image.get("original"),
            width=image.get("width"),
            height=image.get("height"),
        )
    elif kind == "file":
        file = content.get("file") or {}
        out.update(file_name=file.get("filename"), size=file.get("size"))
    elif kind == "todo_list":
        out.update(title=_list_title(content), tasks=tasks(content, tz))
    elif kind in ("board", "column"):
        out["title"] = content.get("title") or ""
        if kind == "board":
            out.update(board_id=element["_id"], url=board_url(element["_id"]))
    elif content.get("textContent"):
        out["text"] = plain(content.get("textContent"))
    if isinstance(content.get("color"), str) and content["color"].isupper():
        out["color"] = content["color"].lower()
    if content.get("labels"):
        out["labels"] = list(content["labels"])
    out["updated_at"] = iso((element.get("meta") or {}).get("modifiedTime"), tz)
    return out


def comments(answer: dict[str, Any], thread_id: str, names: dict[str, str], tz: str) -> list[dict[str, Any]]:
    rows = [c for c in (answer.get("comments") or {}).values() if c.get("threadId") == thread_id]
    rows.sort(key=lambda c: c.get("createdAt") or 0)
    return [
        {
            "comment_id": row["_id"],
            "author": names.get(row.get("userId") or "", "Unknown"),
            "text": plain(row.get("text")),
            "created_at": iso(row.get("createdAt"), tz),
        }
        for row in rows
    ]
