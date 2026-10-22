"""Export board."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from milanote_api_mcp.core.errors import ErrorCode, ToolError
from milanote_api_mcp.core.tools import tool
from milanote_api_mcp.milanote.client import LOCALE, board, board_id, call

if TYPE_CHECKING:
    from milanote_api_mcp.core.context import ToolContext

# format -> what the Export menu sends (recorded 18.10.2026). Text formats come back inline.
_FORMATS: dict[str, dict[str, Any]] = {
    "markdown": {"format": "linear", "fileType": "text/markdown; charset=UTF-8", "includeChildBoards": False},
    "plain_text": {"format": "linear", "fileType": "text/plain; charset=UTF-8", "includeChildBoards": False},
    "word": {
        "format": "linear",
        "fileType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "includeChildBoards": False,
    },
    "pdf": {"format": "canvas", "fileType": "application/pdf", "quality": "regular"},
    "png": {"format": "canvas", "fileType": "image/png"},
}
_INLINE = ("markdown", "plain_text")

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "board_id": {"type": "string", "description": "Board ID from list_boards, or the board URL."},
        "format": {
            "type": "string",
            "enum": list(_FORMATS),
            "description": "markdown, plain_text, word, pdf or png.",
        },
    },
    "required": ["board_id", "format"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "board_id": "1XiqwC1Mir4d4N",
    "format": "markdown",
    "content": "# Novel outline\n\nMaya finds the letter\n\n- [ ] Rewrite act one\n- [x] Pick the ferry scene\n",
    "file_url": "https://media.milanote.com/export/1XiqwC1Mir4d4N/Novel%20outline-261018_1311.md",
}


@tool(
    name="export_board",
    title="Export board",
    access="read",
    confirm=False,
    description="Export a board as Markdown, plain text, Word, PDF or PNG, as the Export menu does.",
    details=(
        "Runs Milanote's own export of one board. markdown and plain_text return the text in content; word, "
        "pdf and png return only file_url. Text formats follow the board's reading order and leave out "
        "comments and sub-board contents; pdf and png are a picture of the canvas. Anyone with file_url can "
        "download the file, and Milanote deletes it after about a day."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /boards/{board_id}/export",
    example_response=EXAMPLE_RESPONSE,
)
async def export_board(ctx: ToolContext, args: dict[str, Any]) -> Any:

    bid = board_id(args.get("board_id"))
    kind = args.get("format")
    if kind not in _FORMATS:
        raise ToolError("format must be markdown, plain_text, word, pdf or png.", ErrorCode.INVALID_INPUT)
    await board(ctx, bid)
    body = {
        **_FORMATS[kind],
        "permissionId": None,
        "locale": LOCALE,
        "timezone": ctx.profile.timezone,
        "emojiStyle": "twitter",
    }
    answer = await call(ctx, "POST", f"/media-service/api/export/{bid}", body=body)
    file_url = answer.get("fileUrl")
    if not file_url:
        raise ToolError("Milanote did not make the export.", ErrorCode.TARGET_ERROR)
    out: dict[str, Any] = {"board_id": bid, "format": kind}
    if kind in _INLINE:
        response = await ctx.call("GET", file_url)
        if response.status != 200:
            raise ToolError("Milanote made the export but the file did not open.", ErrorCode.TARGET_ERROR)
        out["content"] = response.text
    out["file_url"] = file_url
    return out
