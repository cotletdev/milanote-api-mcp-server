# Milanote API and MCP server, self-hosted

<!-- mcp-name: dev.cotlet/milanote -->

A **Milanote API** and a **Milanote MCP server** you run on your own computer, in Python, on the session of your own Google Chrome. 30 of the 31 Milanote tools we run in production at [Cotlet](https://cotlet.dev/integrations/milanote-api-mcp-server): boards, notes, links, to-do lists with due dates, columns, labels, trash, comments, sharing and export.

Milanote has no public API and no official MCP server. This repo gives you both:

- **MCP server** for Claude Code, Claude Desktop, Cursor, Codex and any MCP client, over stdio or HTTP. [Setup](#mcp-server)
- **REST API** on `http://127.0.0.1:8787/api/v1/milanote`, with OpenAPI docs at `/docs`. [Setup](#rest-api)
- **Python**: `call("get_board", board_id="1XiqwC1Mir4d4N")`, plus 9 ready scripts in [`examples/`](https://github.com/cotletdev/milanote-api-mcp-server/blob/main/examples/).

It is for technical people who want to run it themselves, **for noncommercial use only** ([license](#license)). If you want it running 24/7 on a server, kept working when Milanote changes its app, for a team or a business, use the [hosted version at cotlet.dev](https://cotlet.dev/integrations/milanote-api-mcp-server).

[![Milanote MCP server](https://img.shields.io/badge/Milanote%20MCP-30%20tools-6d4aef)](#all-30-tools)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-141318)](#requirements)
[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/license-PolyForm%20Noncommercial-141318)](https://github.com/cotletdev/milanote-api-mcp-server/blob/main/LICENSE)
[![MCP Badge](https://lobehub.com/badge/mcp/cotletdev-milanote-api-mcp-server)](https://lobehub.com/mcp/cotletdev-milanote-api-mcp-server)

```bash
uv tool install milanote-api-mcp                  # or: pip install milanote-api-mcp
milanote-mcp connect                               # reads your Milanote session from Chrome
milanote-mcp call list_boards
claude mcp add milanote -- uvx milanote-api-mcp mcp
```

## Contents

- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Install](#install)
- [Connect your Chrome](#connect-your-chrome)
- [MCP server](#mcp-server)
- [REST API](#rest-api)
- [Python and the example scripts](#python-and-the-example-scripts)
- [All 30 tools](#all-30-tools)
- [Configuration](#configuration)
- [Security and your Milanote account](#security-and-your-milanote-account)
- [Errors](#errors)
- [Self-hosted or hosted](#self-hosted-or-hosted)
- [FAQ](#faq)
- [License](#license)

## How it works

```text
AI agent (MCP) / script (REST, Python) ──▶ milanote-mcp on your computer ──your Milanote cookies──▶ milanote.com
                                                     ▲
                         milanote-mcp connect ───────┘ reads them once from your Chrome (DevTools Protocol)
```

1. You sign in to Milanote in your own Chrome, the way you always do.
2. `milanote-mcp connect` attaches to that Chrome through the Chrome DevTools Protocol, reads the milanote.com cookies and your browser's time zone, and saves them to `~/.config/milanote-api-mcp/session.json`, readable by your user only. It never sees or stores your password.
3. Reads are requests to the JSON endpoints of the Milanote web app on `app.milanote.com/api`. Changes go over the same socket.io channel the web app uses, sent as plain HTTP polling. Everything goes out with your cookies through [curl_cffi](https://github.com/lexiforest/curl_cffi), which copies Chrome's TLS fingerprint. No headless browser runs.

Milanote's session cookie lasts about a month. When Milanote signs you out, the server reads the cookies from Chrome again, if Chrome is open with remote debugging on.

## Requirements

- Python 3.11 or newer.
- Google Chrome 144 or newer, signed in to Milanote. Any Chrome or Chromium works with a [debugging port](#option-b-a-chrome-with-a-debugging-port).
- macOS, Linux or Windows.
- Any Milanote plan. A free account stops at 100 cards, and the tools say so when Milanote refuses. Changing a board someone shared with you needs edit access to it.

## Install

From [PyPI](https://pypi.org/project/milanote-api-mcp/):

```bash
uv tool install milanote-api-mcp       # or: pipx install milanote-api-mcp, or: pip install milanote-api-mcp
milanote-mcp --version
```

MCP clients can also run it with no install: `uvx milanote-api-mcp mcp`.

From source:

```bash
git clone https://github.com/cotletdev/milanote-api-mcp-server.git
cd milanote-api-mcp-server
python3 -m venv .venv
. .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -e .
milanote-mcp --version
```

With [uv](https://docs.astral.sh/uv/): `uv venv && uv pip install -e .`, then `uv run milanote-mcp ...`.

Setting it up with an AI agent (Claude Code, Codex, Cursor)? Open it in this folder and ask it to set up the repo: [`AGENTS.md`](https://github.com/cotletdev/milanote-api-mcp-server/blob/main/AGENTS.md) tells it every step, and it asks you only for the steps in Chrome.

To update: `uv tool upgrade milanote-api-mcp` (or `pip install -U milanote-api-mcp`), from source `git pull && pip install -e .`. We copy every change of the hosted Milanote tools into this repo.

## Connect your Chrome

### Option A: your everyday Chrome (recommended)

1. Open `chrome://inspect/#remote-debugging` in Chrome and switch **remote debugging** on. Chrome then accepts DevTools connections from programs on this computer, and asks you before each one.
2. Make sure you are signed in at [app.milanote.com](https://app.milanote.com).
3. Run:

   ```bash
   milanote-mcp connect
   ```

4. Chrome asks whether to allow the connection. Click **Allow**.

```text
Saved 8 Milanote cookies to /Users/you/.config/milanote-api-mcp/session.json
Signed in to Milanote as Ana Lopez
```

You can switch remote debugging off again afterwards. Leave it on if you want the server to pick up a new session by itself after Milanote signs you out.

`connect` looks for Chrome's `DevToolsActivePort` file in the default profile folder. For Chrome Beta, Canary or a custom profile folder, pass `--profile-dir "<folder>"`.

### Option B: a Chrome with a debugging port

Chrome does not open a debugging port on your default profile, so start a separate one, sign in to Milanote there once, and connect to it:

```bash
# macOS
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-milanote"
# Linux
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-milanote"
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\.chrome-milanote"

milanote-mcp connect --cdp http://127.0.0.1:9222
```

`--cdp` also takes a `ws://` DevTools URL, for example of a Chrome on another machine reached over an SSH tunnel.

### Option C: paste the cookie by hand

For a server with no Chrome: in Chrome open DevTools on app.milanote.com, **Application > Cookies > https://app.milanote.com**, copy the value of `__Secure-milanote.session_token`, then:

```bash
milanote-mcp connect --token       # paste it, input is hidden
# or, without a session file:
export MILANOTE_AUTH_TOKEN=...
```

A pasted token is not refreshed on its own. Paste a new one when Milanote signs you out. Times then come in this machine's time zone.

Check the session at any time:

```bash
milanote-mcp status
```

## MCP server

The MCP server lists every tool with its input schema, a description written for agents, and hints: read tools are marked read-only, and tools that comment, invite, publish or trash are marked so your client asks before running them.

### Claude Code

```bash
claude mcp add milanote -- uvx milanote-api-mcp mcp
# read only:
claude mcp add milanote -- uvx milanote-api-mcp mcp --read-only
```

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "milanote": {
      "command": "uvx",
      "args": ["milanote-api-mcp", "mcp"]
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json`, the same block as Claude Desktop. A ready copy is in [`mcp.json`](https://github.com/cotletdev/milanote-api-mcp-server/blob/main/mcp.json).

### Codex

`~/.codex/config.toml`:

```toml
[mcp_servers.milanote]
command = "uvx"
args = ["milanote-api-mcp", "mcp"]
```

### Over HTTP

`milanote-mcp serve` also serves MCP over streamable HTTP at `http://127.0.0.1:8787/mcp`, for clients that take a URL:

```bash
milanote-mcp serve
claude mcp add --transport http milanote http://127.0.0.1:8787/mcp
```

Then ask your agent things like:

> *Put these 12 reference links on the Moodboard sub-board of Brand refresh and skip the ones already there.*
>
> *Export my Novel outline board and each chapter sub-board as Markdown into ./outline.*
>
> *Here are my call notes. Add the action items as a to-do list on Q1 campaign with the dates we agreed.*
>
> *Where did I save that note about the color palette?*

## REST API

```bash
milanote-mcp serve                 # http://127.0.0.1:8787, MCP at /mcp, docs at /docs
```

Each tool has its own route under `/api/v1/milanote`, the same paths as the hosted API at cotlet.dev, so code written against one works with the other. Path parts and the query string are arguments, and a JSON body adds the rest.

```bash
curl 'http://127.0.0.1:8787/api/v1/milanote/boards'
curl 'http://127.0.0.1:8787/api/v1/milanote/boards/1XiqwC1Mir4d4N'
curl -X POST http://127.0.0.1:8787/api/v1/milanote/boards/1XiqwC1Mir4d4N/notes \
  -H 'Content-Type: application/json' \
  -d '{"text": "Kickoff moved to Tuesday."}'
```

Any tool by name, body as its arguments:

```bash
curl -X POST http://127.0.0.1:8787/api/v1/milanote/tools/export_board -d '{"board_id": "1XiqwC1Mir4d4N", "format": "markdown"}'
```

- `GET /api/v1/milanote/tools`: every tool with its route, input schema and an example answer.
- `GET /docs`: interactive OpenAPI docs, `GET /openapi.json` the schema, for n8n, Postman or a generated client.
- Answers are JSON. Lists that stop early return `has_more: true`; raise `limit` to get the rest.

The server listens on `127.0.0.1` only. To reach it from another device of yours, set a token, and every request then needs `Authorization: Bearer <token>`:

```bash
MILANOTE_MCP_TOKEN=$(openssl rand -hex 24) milanote-mcp serve --host 0.0.0.0
```

## Python and the example scripts

Straight from Python, no server needed:

```python
from milanote_api_mcp import call

boards = call("list_boards")["boards"]
board = call("get_board", board_id=boards[0]["id"])
call(
    "add_todo_list",
    board_id=board["board_id"],
    title="This week",
    tasks=[{"text": "Send the brief", "due_date": "2026-10-28"}, {"text": "Book the photographer"}],
)
```

Or one tool from the shell: `milanote-mcp call get_board board_id=1XiqwC1Mir4d4N`, or with a JSON object.

Ready scripts in [`examples/`](https://github.com/cotletdev/milanote-api-mcp-server/blob/main/examples/). Each takes `--help`, and the ones that list things print JSON or save `--out file.csv` / `--out file.json`:

| Script | What it does |
|---|---|
| [`list_boards.py`](https://github.com/cotletdev/milanote-api-mcp-server/blob/main/examples/list_boards.py) | Your boards as a tree, from Home or any board, `--depth` levels down. |
| [`search_boards.py`](https://github.com/cotletdev/milanote-api-mcp-server/blob/main/examples/search_boards.py) | Searches all your boards and prints each matching card with its board and path. |
| [`export_boards.py`](https://github.com/cotletdev/milanote-api-mcp-server/blob/main/examples/export_boards.py) | A board and its sub-boards to Markdown, text, Word, PDF or PNG, one file per board, folders following the nesting. |
| [`board_card_counts.py`](https://github.com/cotletdev/milanote-api-mcp-server/blob/main/examples/board_card_counts.py) | Cards on each board by type, biggest first, and your use of the free plan's limit. |
| [`open_tasks.py`](https://github.com/cotletdev/milanote-api-mcp-server/blob/main/examples/open_tasks.py) | Unticked tasks from every to-do list on a board and its sub-boards, soonest due first. `--due-before`. |
| [`save_links.py`](https://github.com/cotletdev/milanote-api-mcp-server/blob/main/examples/save_links.py) | Saves a list of URLs as link cards, skipping the ones already on the board. `--dry-run` first. |
| [`add_todo_list.py`](https://github.com/cotletdev/milanote-api-mcp-server/blob/main/examples/add_todo_list.py) | A to-do list from a text file, one task per line, with optional `YYYY-MM-DD HH:MM` due dates. |
| [`add_note.py`](https://github.com/cotletdev/milanote-api-mcp-server/blob/main/examples/add_note.py) | A note card from `--text`, a file or standard input. |
| [`publish_board.py`](https://github.com/cotletdev/milanote-api-mcp-server/blob/main/examples/publish_board.py) | Turns a board's read-only link on and prints it, or `--off`. |

```bash
python examples/export_boards.py --board 1XiqwC1Mir4d4N --dir ./outline
python examples/save_links.py --board 1XiqwC1Mir4d4N --file links.txt --dry-run
```

On a schedule, cron on your own computer works while it is on: `0 18 * * 5 cd ~/milanote-api-mcp-server && .venv/bin/python examples/export_boards.py --board 1XiqwC1Mir4d4N --dir ~/backups/milanote`.

## All 30 tools

`board_id` is the ID from `list_boards`, or the board's URL (`https://app.milanote.com/1XiqwC1Mir4d4N/...`). Cards the tools add land in the board's Unsorted panel, the same place Milanote puts uploads, so they never cover cards on the canvas. `milanote-mcp tools` prints this list, `milanote-mcp tools --json` adds the input schemas.

### Boards

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `list_boards` | read | `GET /boards` | Boards inside one board, by default the boards on your Home, with title, ID and link. |
| `list_recent_boards` | read | `GET /boards/recent` | Boards you opened lately, newest first, wherever they sit in your board tree. |
| `search_boards` | read | `GET /boards/search` | Find boards and cards by text across your boards, like the Search icon in Milanote. |
| `get_board` | read | `GET /boards/{board_id}` | Every card on a board: notes, links, images, files, to-do lists, columns and sub-boards. |
| `create_board` | write | `POST /boards` | New board on your Home or nested inside another board. |
| `rename_board` | write | `PATCH /boards/{board_id}` | Change a board's title. |
| `duplicate_board` | write | `POST /boards/{board_id}/duplicate` | Copy a board with everything on it, sub-boards included, as a template. |
| `export_board` | read | `GET /boards/{board_id}/export` | Export a board as Markdown, plain text, Word, PDF or PNG, as the Export menu does. |

### Cards

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `add_note` | write | `POST /boards/{board_id}/notes` | Note card with plain text, added to a board's Unsorted panel. |
| `edit_note` | write | `PATCH /boards/{board_id}/notes/{card_id}` | Replace the text of a note card. |
| `add_link` | write | `POST /boards/{board_id}/links` | Link card for a web address, with the page's title and preview, added to Unsorted. |
| `add_todo_list` | write | `POST /boards/{board_id}/todo-lists` | To-do list card with tasks, each with an optional due date and time, added to Unsorted. |
| `set_task_done` | write | `PUT /boards/{board_id}/cards/{card_id}/tasks/{task}/done` | Tick or untick one task in a to-do list. |
| `add_column` | write | `POST /boards/{board_id}/columns` | Empty column on a board, to group cards in a stack. |

### Arrange cards

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `move_card` | write | `POST /boards/{board_id}/cards/{card_id}/move` | Move a card or a sub-board to another board, or into or out of a column. |
| `set_card_color` | write | `PUT /boards/{board_id}/cards/{card_id}/color` | Colour the bar on top of a note, to-do list, link, file or column, or clear it. |
| `add_label` | write | `POST /boards/{board_id}/cards/{card_id}/labels` | Put a label on a card, creating the label when the name is new. |
| `list_labels` | read | `GET /labels` | The labels you can put on cards, with name and colour. |

### Trash

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `trash_cards` | write | `POST /boards/{board_id}/cards/trash` | Move cards or sub-boards to the trash, as the Delete key does. |
| `list_trash` | read | `GET /trash` | Cards and boards you moved to the trash, with the board each one came from. |
| `restore_card` | write | `POST /trash/{card_id}/restore` | Take a card or board out of the trash and put it back where it was. |

### Comments

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `add_comment` | write | `POST /boards/{board_id}/comments` | Comment card on a board, or a reply in a comment thread, posted under your name. |
| `edit_comment` | write | `PATCH /boards/{board_id}/comments/{comment_id}` | Replace the text of a comment you wrote. |
| `delete_comment` | write | `DELETE /boards/{board_id}/comments/{comment_id}` | Delete a comment you wrote, for everyone. |

### Sharing

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `get_sharing` | read | `GET /boards/{board_id}/sharing` | Who can open a board: owner, editors and the read-only link with its settings. |
| `invite_editor` | write | `POST /boards/{board_id}/editors` | Invite someone by email to edit a board and the boards inside it. |
| `remove_editor` | write | `DELETE /boards/{board_id}/editors` | Take away someone's access to a board, or cancel an invite they have not accepted. |
| `publish_board` | write | `POST /boards/{board_id}/publish` | Turn on a board's read-only link, which anyone can open without signing up. |
| `unpublish_board` | write | `DELETE /boards/{board_id}/publish` | Turn off a board's read-only link; people who had it can no longer open the board. |

### Account

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `get_usage` | read | `GET /usage` | How many cards your account uses against the free plan's limit, by card type. |

### Not in this version

| Tool | Why |
|---|---|
| `upload_image` | On the hosted version it takes the image as a link, an upload or base64 through Cotlet's file handling, which this repo does not have yet. Upload images in Milanote, or use the hosted tool. |

Never built, on purpose: your Milanote sign-in, email, password and profile settings, and plans and billing.

## Configuration

| Variable | Default | What it does |
|---|---|---|
| `MILANOTE_MCP_HOME` | `~/.config/milanote-api-mcp` | Folder of `session.json`. |
| `MILANOTE_AUTH_TOKEN` | | Milanote `__Secure-milanote.session_token` cookie, instead of `milanote-mcp connect`. |
| `MILANOTE_PROXY` | | Proxy for every request to Milanote, e.g. `http://user:pass@host:port`. |
| `MILANOTE_MCP_READ_ONLY` | | `1` hides and refuses every tool that changes Milanote (same as `--read-only`). |
| `MILANOTE_MCP_TOKEN` | | Bearer token required by `serve`; needed to listen beyond `127.0.0.1`. |
| `MILANOTE_MCP_HOST`, `MILANOTE_MCP_PORT` | `127.0.0.1`, `8787` | Address of `serve`. |

## Security and your Milanote account

- **Your password never reaches this code.** Only cookies are read, and only those of milanote.com.
- **The session file is yours.** `session.json` is created with mode 0600. Anyone who has it can act as you on Milanote, so keep it out of git and shared folders.
- **Local by default.** `serve` binds to `127.0.0.1` and refuses another address without `MILANOTE_MCP_TOKEN`.
- **milanote.com only.** Requests and redirects outside milanote.com are refused.
- **Read-only mode.** `--read-only` or `MILANOTE_MCP_READ_ONLY=1` exposes the 9 read tools only.
- **Some actions reach other people.** Comments carry your name, `invite_editor` emails the person you invite, and `publish_board` makes a board readable by anyone with the link. MCP clients ask before running them; a script does not.
- **Trash is reversible, comments are not.** `trash_cards` moves cards to the board's trash, and `restore_card` brings them back. `delete_comment` deletes for everyone.

## Errors

The REST API answers `{"error": "<code>", "message": "..."}`. The MCP server returns the same code and message as a tool error.

| Status | Code | What to do |
|---|---|---|
| 401 | `auth_required`, `auth_expired` | No session, or Milanote signed you out. Sign in to Milanote in Chrome and run `milanote-mcp connect`. |
| 403 | `scope_denied` | The server runs read-only. |
| 403 | `target_blocked` | Milanote refused the request or showed a bot check. Open app.milanote.com in Chrome once, then retry. |
| 422 | `invalid_input` | An argument is missing or wrong; the message names it. |
| 429 | `rate_limited` | Milanote is limiting the account. Wait a few minutes. |
| 502 | `target_error` | Milanote answered with an error, for example the free plan's card limit, or changed its app. `git pull` for the latest tools, or [open an issue](https://github.com/cotletdev/milanote-api-mcp-server/issues). |
| 504 | `timeout` | Milanote did not confirm a change in time. Check the board before you retry, the change may have landed. |

## Self-hosted or hosted

| | This repo | [Cotlet, hosted](https://cotlet.dev/integrations/milanote-api-mcp-server) |
|---|---|---|
| Tools | 30 | 31, `upload_image` included |
| Runs | on your computer, while it is on | in the cloud, 24/7 |
| Milanote session | your Chrome, cookies in a local file | your own Cloud Browser in the EU, profile encrypted with AES-256-GCM |
| When Milanote changes its app | `git pull` once we have fixed it | fixed for you, every tool tested daily |
| Approvals | your MCP client asks per call | comments, invites, publishing and trash wait for your OK, switchable per tool |
| Works with | MCP clients on your machine, local scripts | Claude.ai and ChatGPT connectors, n8n, Make, Zapier, any HTTP client |
| Who may use it | you, for noncommercial use | teams, businesses, agencies |
| Price | free | free 7-day trial with 2,000 credits, no card; then one-time packs from $29 for 5,000 credits |

On the hosted version a successful call uses 20 to 30 credits (25 for most tools), failed calls are free, and the Cloud Browser uses 50 credits a day while it has an app enabled for agents. [Full pricing](https://cotlet.dev/pricing).

## FAQ

**Does Milanote have an official API?**
No. Milanote has no public API, no webhooks and no official MCP server (checked October 2026). A public API and an MCP server are open requests on its public roadmap, and the only way to get content out is the Export button, one board at a time. Details: [cotlet.dev/integrations/milanote-api-mcp-server](https://cotlet.dev/integrations/milanote-api-mcp-server).

**Is there a Milanote MCP server for Claude, ChatGPT or Cursor?**
Yes, this one runs on your machine: `milanote-mcp mcp` for Claude Code, Claude Desktop, Cursor and Codex. ChatGPT and Claude.ai connectors need a public HTTPS URL, which the [hosted Milanote MCP server](https://cotlet.dev/integrations/milanote-api-mcp-server) gives you.

**Can I export Milanote boards to Markdown?**
Yes, with sub-boards: `python examples/export_boards.py --board <board URL> --dir ./outline` writes one Markdown file per board, in folders that follow the nesting. Word, PDF, PNG and plain text work the same way with `--format`.

**Can I back up all my boards?**
Run `export_boards.py` on each board of your Home, from cron. Images and files on a board stay in Milanote. Milanote's own Generate ZIP in the Export menu downloads the originals.

**Can it add to boards someone shared with me?**
Yes, if your account can edit that board. Read-only boards can be read and exported, not changed.

**Does it work on the free plan?**
Yes. The free plan's 100-card limit still applies: `get_usage` shows where you stand, and adding a card past it fails with Milanote's own message.

**Why does it need my Chrome?**
To read your Milanote session without your password, and your time zone for due dates. Chrome is used once per sign-in, not for each call.

**What happens when Milanote signs me out?**
Calls fail with `auth_expired`. With Chrome remote debugging on, the server reads the new cookies on the next call (click Allow when Chrome asks); otherwise run `milanote-mcp connect` again.

**Can it run on a VPS or in Docker?**
Technically yes, with `MILANOTE_AUTH_TOKEN`. Milanote then sees your session from a datacenter IP, which looks less like you. For an always-on setup the hosted version keeps your session in your own Cloud Browser on a fixed IP.

**Will my Milanote account get banned?**
Requests carry Chrome's fingerprint and go out one at a time, as you would click. Nobody can promise a platform never acts. Keep to your normal use.

**Can I use it at work or for my clients?**
No, the license allows noncommercial use only. For a team, a company or client work, use [Cotlet](https://cotlet.dev) or write to [contact@cotlet.dev](mailto:contact@cotlet.dev).

**Is it open source?**
The source is public, the license is not an open source license: noncommercial use only, no business use.

**A tool broke or I need another one.**
[Open an issue](https://github.com/cotletdev/milanote-api-mcp-server/issues) with the tool name and the error message.

## License

[PolyForm Noncommercial License 1.0.0](https://github.com/cotletdev/milanote-api-mcp-server/blob/main/LICENSE). In short:

- **Allowed:** noncommercial use: you, for your own personal purposes with your own Milanote account, or a charity, school, public research or government body. Changing the code, and sharing it under the same license.
- **Not allowed:** any commercial use, your own business included; client work; selling or offering it, or a service built on it.

---

<p>
  <a href="https://cotlet.dev">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="assets/logo-white.svg">
      <img src="https://raw.githubusercontent.com/cotletdev/milanote-api-mcp-server/main/assets/logo.svg" alt="Cotlet" width="120">
    </picture>
  </a>
</p>

Maintained by [Cotlet](https://cotlet.dev) ([@cotletdev](https://x.com/cotletdev)). Milanote is a trademark of its owner. This project is unofficial and not affiliated with, endorsed or sponsored by Milanote.
