"""Who is signed in: Milanote's own answer for the account (app.milanote.com/api/users/me)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from milanote_api_mcp.core.errors import AuthExpiredError, ErrorCode, ToolError
from milanote_api_mcp.milanote.sync import APP

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext


async def whoami(ctx: ToolContext) -> str | None:
    """None only when Milanote says signed out (401); any other failure raises (detection tries again later)."""
    try:
        response = await ctx.call("GET", f"{APP}/api/users/me", headers={"accept": "application/json"})
    except AuthExpiredError:
        return None
    if response.status != 200:
        raise ToolError(f"Milanote answered {response.status} to who am I.", ErrorCode.TARGET_ERROR)
    user = (response.json() or {}).get("user") or {}
    if not user.get("_id"):
        return None
    name = (user.get("name") or {}).get("displayName") or ""
    return name or user.get("email") or None
