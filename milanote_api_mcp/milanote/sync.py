"""Milanote's write channel: socket.io (Engine.IO 4) over HTTP long polling, recorded 18.10.2026.

The web app sends every change (new card, edit, move to trash, comment) as an `action` event on its socket.io
connection and waits for the ack `[{"status": 200}]`. The same server answers the polling transport, so the
this server sends the identical events by plain requests: open (GET), connect (POST "40"), then one POST per event
and GETs until its ack arrives. Element ids are made on the client: base62 seconds, the clientId Milanote hands
out with every /api/users/me, and a per-client counter.
"""

from __future__ import annotations

import json
import secrets
import time
from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

APP = "https://app.milanote.com"
_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_SEPARATOR = "\x1e"
_TEXT = {"content-type": "text/plain;charset=UTF-8", "accept": "*/*"}
# Long polls the ack may need: the server holds a GET up to its 25 s ping interval when nothing is queued,
# so two keep a write inside the tool's time limit.
_ACK_POLLS = 2


def base62(number: int) -> str:
    out = ""
    while True:
        number, rest = divmod(number, 62)
        out = _ALPHABET[rest] + out
        if not number:
            return out


class Sync:
    """One polling connection for one execution, bound to the signed-in user."""

    def __init__(self, ctx: ToolContext, user: dict[str, Any]) -> None:
        self._ctx = ctx
        self.user_id: str = user["_id"]
        self._client_id: str = user.get("clientId") or base62(secrets.randbelow(62**6)).rjust(6, "0")
        self._tick: int = int(user.get("clientTick") or 0)
        self._url = f"{APP}/socket.io/?userId={self.user_id}&EIO=4&transport=polling"
        self._ack = 0
        self._device = f"mdid-{base62(int(time.time()))}{secrets.token_hex(2)}"
        self._session = f"msid-{base62(int(time.time()))}{secrets.token_hex(2)}"

    def new_id(self) -> str:
        """A fresh element id in Milanote's own format, e.g. 1XiqwC1Mir4d4N."""
        self._tick += 1
        return base62(int(time.time())) + self._client_id + base62(self._tick)

    async def _get(self) -> list[str]:
        response = await self._ctx.call("GET", self._url, headers={"accept": "*/*"})
        if response.status != 200:
            raise ToolError(f"Milanote refused the connection ({response.status}).", ErrorCode.TARGET_ERROR)
        return response.text.split(_SEPARATOR)

    async def _post(self, packet: str) -> None:
        response = await self._ctx.call("POST", self._url, data=packet.encode(), headers=_TEXT)
        if response.status != 200:
            raise ToolError(f"Milanote refused the change ({response.status}).", ErrorCode.TARGET_ERROR)

    async def open(self) -> Sync:
        packets = await self._get()
        try:
            sid = json.loads(packets[0][1:])["sid"]
        except (ValueError, KeyError, IndexError) as exc:
            raise ToolError("Milanote did not open a connection.", ErrorCode.TARGET_ERROR) from exc
        self._url += f"&sid={sid}"
        await self._post("40")
        if not any(packet.startswith("40") for packet in await self._get()):
            raise ToolError("Milanote did not accept the connection.", ErrorCode.TARGET_ERROR)
        return self

    async def close(self) -> None:
        await self._post("1")

    def stamp(self, action: dict[str, Any], channels: list[str]) -> dict[str, Any]:
        """The fields the web app adds to every action it syncs."""
        return {
            **action,
            "sync": True,
            "user": {"_id": self.user_id, "clientId": self._client_id, "clientTick": self._tick},
            "tokens": [],
            "deviceId": self._device,
            "sessionId": self._session,
            "channels": channels,
        }

    async def send(self, action: dict[str, Any], channels: list[str]) -> None:
        """Emits one action and waits for Milanote's ack; any status but 200 is an error."""
        ack = self._ack
        self._ack += 1
        await self._post(f"42{ack}" + json.dumps(["action", self.stamp(action, channels)], separators=(",", ":")))
        prefix = f"43{ack}"
        for _ in range(_ACK_POLLS):
            for packet in await self._get():
                if packet == "2":
                    await self._post("3")
                elif packet.startswith(prefix):
                    try:
                        answer = json.loads(packet[len(prefix) :] or "[{}]")
                        status = (answer[0] or {}).get("status") if answer else None
                    except (ValueError, AttributeError, TypeError):
                        status = None
                    if status != 200:
                        raise ToolError(f"Milanote rejected the change ({status}).", ErrorCode.TARGET_ERROR)
                    return
                elif packet.startswith("41"):
                    raise ToolError("Milanote closed the connection.", ErrorCode.TARGET_ERROR)
        raise ToolError("Milanote did not confirm the change in time.", ErrorCode.TIMEOUT)

    def meta(self) -> dict[str, Any]:
        now = int(time.time() * 1000)
        return {
            "creator": self.user_id,
            "modifiedBy": self.user_id,
            "createdTime": now,
            "modifiedTime": now,
            "platform": "Desktop web",
            "locationSectionModifiedTime": now,
        }

    async def create(
        self, element_id: str, element_type: str, location: dict[str, Any], content: dict[str, Any]
    ) -> None:
        now = int(time.time() * 1000)
        action = {
            "id": element_id,
            "location": location,
            "content": content,
            "meta": self.meta(),
            "elementType": element_type,
            "type": "ELEMENT_CREATE",
            "timestamp": now,
            "creationSource": "TOOLBAR",
            "markAsFetched": True,
            "activity": {"track": False, "boardId": location["parentId"]},
        }
        await self.send(action, [location["parentId"]])

    async def update(self, element_id: str, board_id: str, changes: dict[str, Any]) -> None:
        action = {
            "type": "ELEMENT_UPDATE",
            "updates": [{"id": element_id, "changes": changes}],
            "timestamp": int(time.time() * 1000),
            "recalculateChannels": False,
            "activity": {"track": False, "boardId": board_id},
        }
        await self.send(action, [board_id])
