# AGENTS.md

You are an AI agent in a clone of this repo. It is a self-hosted Milanote API and MCP server: 30 tools that work in the user's own Milanote account, through the session of their own Google Chrome. Your usual job is one of three: set it up for the user, use its tools for them, or change its code. Human docs: `README.md`.

## Before you start

- The license allows noncommercial use only (PolyForm Noncommercial 1.0.0, `LICENSE`). If the user is setting this up for a company, a team or clients, say so and point to the hosted version at https://cotlet.dev/integrations/milanote-api-mcp-server. Do not continue the setup for that use.
- Every tool acts as the user on Milanote. Tools with access `write` change boards, and some reach other people: `add_comment` posts under the user's name, `invite_editor` emails an invitation, `publish_board` makes a board readable by anyone with the link.

## Set it up for the user

Do the steps yourself. Ask the user only for what needs their hands in Chrome.

1. Check Python: `python3 --version` must be 3.11 or newer.
2. Install in the repo root:

   ```bash
   python3 -m venv .venv && .venv/bin/pip install -e .
   .venv/bin/milanote-mcp --version
   ```

   On Windows the path is `.venv\Scripts\milanote-mcp`. With uv: `uv venv && uv pip install -e .`.
3. Ask the user to do two things in Chrome. You cannot open `chrome://` pages for them.
   - Open `chrome://inspect/#remote-debugging` and switch remote debugging on.
   - Be signed in at https://app.milanote.com.
4. Run `.venv/bin/milanote-mcp connect`. Tell the user to click **Allow** when Chrome asks about the connection. Success prints `Signed in to Milanote as <name>`.
5. Check: `.venv/bin/milanote-mcp status`, then `.venv/bin/milanote-mcp call list_boards`.
6. Add the MCP server to the user's client. Use the absolute path of `.venv/bin/milanote-mcp`:
   - Claude Code: `claude mcp add milanote -- <abs path>/.venv/bin/milanote-mcp mcp`
   - Claude Desktop, Cursor, Codex: the config blocks in `README.md`, section "MCP server".
   - Add `--read-only` after `mcp` if the user only wants to read.
   The client loads new MCP servers on its next start. Tell the user.

If step 4 fails:

| Message | What to do |
|---|---|
| `Chrome remote debugging is off` | Step 3 is not done, or Chrome is Beta, Canary or a custom profile: pass `--profile-dir "<profile folder>"`. |
| `Could not connect to Chrome` | The user did not click Allow, or Chrome is closed. Run `connect` again. |
| `This Chrome is not signed in to Milanote` | The user signs in at app.milanote.com in that Chrome, then run `connect` again. |
| No Chrome on this machine (a server) | The user copies the `__Secure-milanote.session_token` cookie from Chrome DevTools (Application, Cookies, https://app.milanote.com) and runs `milanote-mcp connect --token` themselves. Never ask them to paste the token into the chat. |

## Use the tools

- With the MCP server added, call its tools. Without it: `.venv/bin/milanote-mcp call <tool> key=value ...`, or one JSON object as the argument.
- `.venv/bin/milanote-mcp tools` lists every tool with access and route. `tools --json` adds the input schemas.
- Start with `list_boards`. Its `id` values are the `board_id` every other tool takes; a board URL works too. Sub-boards come from `list_boards` with `parent_board_id`, or as cards of type `board` in `get_board`.
- New cards land in the board's Unsorted panel. A free account stops at 100 cards: check `get_usage` before adding many.
- Lists return `has_more`. Raise `limit` to get the rest.
- Before a `write` tool, show the user what you will change and where, and get their OK. To undo a card you added, `trash_cards` it; `restore_card` brings it back.
- For a script or a cron job, use `milanote_api_mcp.scripting` (`call`, `write_rows`) and the scripts in `examples/` as models.
- For a REST API (n8n, other languages): `.venv/bin/milanote-mcp serve`, routes under `http://127.0.0.1:8787/api/v1/milanote`, docs at `/docs`.

Errors come as `<code>: <message>`. `auth_expired` means Milanote signed the session out: the user signs in again in Chrome and you run `connect`. `timeout` on a write means Milanote did not confirm it in time: read the board before you retry. More codes: `README.md`, section "Errors".

## Keep secrets out

- `~/.config/milanote-api-mcp/session.json` and `MILANOTE_AUTH_TOKEN` give full access to the user's Milanote account. Never print, log, commit or copy their content.
- `serve` listens on 127.0.0.1. Never start it on another address without `MILANOTE_MCP_TOKEN`.

## Change the code

| Path | What | Edit? |
|---|---|---|
| `milanote_api_mcp/milanote/` | the Milanote tools, one file per tool in `tools/`, shared request code in `client.py`, the write channel in `sync.py` | Yes for a local fix, but the next `git pull` brings our version of these files. Report the bug at https://github.com/cotletdev/milanote-api-mcp-server/issues |
| `milanote_api_mcp/app.py` | app name, domains, session cookie, REST prefix | Rarely |
| `milanote_api_mcp/core/` | `@tool` declaration, errors, the HTTP client with the session (`context.py`), the account guard | Yes |
| `milanote_api_mcp/session.py` | reading cookies and the time zone from Chrome over CDP, the session file | Yes |
| `milanote_api_mcp/runner.py`, `api.py`, `mcp_server.py`, `cli.py` | tool registry, REST API, MCP server, command line | Yes |
| `examples/` | scripts for common jobs | Yes |

A new tool is a new file in `milanote_api_mcp/milanote/tools/` with a `@tool(...)` declaration (name, access, input schema, `route`). The registry finds it, and the REST API, the MCP server and the CLI show it without other changes.

There is no test suite. After a change, run `.venv/bin/milanote-mcp tools` and one read tool against the user's account.
