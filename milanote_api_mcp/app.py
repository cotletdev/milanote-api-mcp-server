"""Everything the server knows about Milanote outside `milanote/`: names, domains and the session cookie.

The rest of the package reads these values and never names the app itself.
"""

from __future__ import annotations

NAME = "Milanote"
SLUG = "milanote"
# The command and the prefix of every environment variable (MILANOTE_AUTH_TOKEN, MILANOTE_MCP_TOKEN ...).
CLI = "milanote-mcp"
ENV = "MILANOTE"
# Requests may reach only these hosts and their subdomains. Their cookies are read from Chrome.
DOMAINS = ("milanote.com",)
# Present only while signed in. The first is the cookie a pasted token sets.
SESSION_COOKIES = ("__Secure-milanote.session_token",)
COOKIE_DOMAIN = "app.milanote.com"
LOGIN_URL = "https://app.milanote.com/login"
# A final URL with one of these means the app signed the session out.
LOGGED_OUT_MARKERS = ("/login",)
# An answer with one of these asks you to sign in again before a sensitive action. Milanote has none.
RELOGIN_MARKERS: tuple[str, ...] = ()
# Paths of your Milanote account that tools may read but never write to, on top of the common password,
# email and sign-in paths. Milanote's tools touch none.
ACCOUNT_PATHS: tuple[str, ...] = ()
# REST routes live under this path, the same as on cotlet.dev.
API_PREFIX = "/api/v1/milanote"
# Prepended to the MCP server's instructions: where an agent starts.
AGENT_START = "Start with list_boards: its `board_id` values are what every other tool takes."
