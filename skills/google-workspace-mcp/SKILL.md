---
name: google-workspace-mcp
description: Use when the user wants to read/edit Google Docs from Claude, refresh expired Google Workspace MCP tokens, troubleshoot google-workspace MCP errors, change OAuth scopes, or says "переавторизуй google", "google docs не работает", "fix google mcp", "re-auth google", "обнови токены google". Knows the OAuth gotchas (Web vs Desktop client, restricted scope, browser cache, Test users) and the operational recipes.
version: 1.0.0
tags: [mcp, google, oauth, infrastructure]
---

# Google Workspace MCP

User-scope MCP `google-workspace` (package `workspace-mcp`, taylorwilsdon) gives all Claude agents read+edit access to Google Docs and Drive. This skill is the operational playbook for it.

For full setup history and rationale, see `${OBSIDIAN_VAULT}/general/Knowledge/google-workspace-mcp.md`.

## Quick state check

If something's off, first verify state:

```bash
# Is MCP registered?
claude mcp list | grep google-workspace

# Do credentials exist?
ls -la ~/.config/google-workspace-mcp/client_secret.json
ls -la ~/.config/google-workspace-mcp/credentials/zeyka666@gmail.com.json

# Token scopes + freshness
python3 -c "
import json
c = json.load(open('/Users/andrey/.config/google-workspace-mcp/credentials/zeyka666@gmail.com.json'))
print('scopes:', len(c.get('scopes', [])))
print('expiry:', c.get('expiry'))
print('has refresh_token:', bool(c.get('refresh_token')))"
```

## Recipe 1 — Re-auth (most common task, every ~7 days while app is in Testing)

```bash
~/.config/google-workspace-mcp/reauth.sh
```

The script:
1. Kills any stale workspace-mcp HTTP server on :8000
2. Starts a fresh one (env vars baked in)
3. Calls `start_google_auth` and prints + opens the auth URL in Chrome incognito (also copies to clipboard)
4. Waits for ENTER in terminal after the user completes browser flow
5. Cleans up

**Critical**: user MUST open the auth URL in an **incognito/private window** under the correct Google account (`Zeyka666@gmail.com`). A regular window often returns `invalid_client` due to multi-account session caching — verified empirically that the URL works via `curl` even when the user's browser says otherwise.

## Recipe 2 — Re-auth manually (when the script isn't enough)

```bash
# 1. Stop any stale server
pkill -f "workspace-mcp.*streamable-http"; sleep 1

# 2. Start bootstrap server
GOOGLE_CLIENT_SECRET_PATH=/Users/andrey/.config/google-workspace-mcp/client_secret.json \
WORKSPACE_MCP_CREDENTIALS_DIR=/Users/andrey/.config/google-workspace-mcp/credentials \
USER_GOOGLE_EMAIL=Zeyka666@gmail.com \
WORKSPACE_MCP_PORT=8000 \
OAUTHLIB_INSECURE_TRANSPORT=1 \
nohup uvx --from workspace-mcp workspace-mcp --single-user --tools docs drive --transport streamable-http \
  > /tmp/wmcp.log 2>&1 &

sleep 5 && curl -s http://localhost:8000/health

# 3. Get fresh auth URL
uvx --from workspace-mcp workspace-cli --url http://localhost:8000/mcp \
  call start_google_auth service_name=docs user_google_email=Zeyka666@gmail.com

# 4. Hand the URL to user. They open it in INCOGNITO.
# 5. After "Authentication Successful" page → stop server:
pkill -f "workspace-mcp.*streamable-http"
```

## Recipe 3 — Verify it works end-to-end

```bash
# Start HTTP server (as in Recipe 2 step 2)
# Then read a known doc:
uvx --from workspace-mcp workspace-cli --url http://localhost:8000/mcp \
  call get_doc_as_markdown \
    document_id=<DOC_ID> \
    user_google_email=Zeyka666@gmail.com
# Stop server.
```

`<DOC_ID>` is the path segment from a Google Docs URL: `docs.google.com/document/d/<DOC_ID>/edit`.

## Recipe 4 — Drop full `drive` scope (if Production publish blocks it)

Full `drive` is a Google-classified **restricted** scope. If user publishes the app to Production unverified and gets blocked, downgrade scopes:

```bash
claude mcp remove google-workspace --scope user
claude mcp add -s user google-workspace \
  -e GOOGLE_CLIENT_SECRET_PATH=/Users/andrey/.config/google-workspace-mcp/client_secret.json \
  -e WORKSPACE_MCP_CREDENTIALS_DIR=/Users/andrey/.config/google-workspace-mcp/credentials \
  -e USER_GOOGLE_EMAIL=Zeyka666@gmail.com \
  -e WORKSPACE_MCP_PORT=8000 \
  -e OAUTHLIB_INSECURE_TRANSPORT=1 \
  -- uvx --from workspace-mcp workspace-mcp --single-user \
       --permissions docs:full drive:readonly --transport stdio
```

Then delete cached token (it has the now-too-broad scopes) and re-auth:
```bash
rm ~/.config/google-workspace-mcp/credentials/zeyka666@gmail.com.json
~/.config/google-workspace-mcp/reauth.sh
```

## Recipe 5 — Add more services (Sheets, Gmail, Calendar)

```bash
claude mcp remove google-workspace --scope user
claude mcp add -s user google-workspace \
  -e GOOGLE_CLIENT_SECRET_PATH=/Users/andrey/.config/google-workspace-mcp/client_secret.json \
  -e WORKSPACE_MCP_CREDENTIALS_DIR=/Users/andrey/.config/google-workspace-mcp/credentials \
  -e USER_GOOGLE_EMAIL=Zeyka666@gmail.com \
  -e WORKSPACE_MCP_PORT=8000 \
  -e OAUTHLIB_INSECURE_TRANSPORT=1 \
  -- uvx --from workspace-mcp workspace-mcp --single-user \
       --tools docs drive sheets gmail calendar --transport stdio
```

Then re-auth — Google will request consent for the new scopes.

## Known traps (don't repeat past mistakes)

1. **Use Web application OAuth client type, NOT Desktop.** Desktop type returns HTTP 400 because Google's loopback policy doesn't match `http://localhost:8000/oauth2callback` against the Desktop client's bare `http://localhost` registered URI. The workspace-mcp README incorrectly suggests Desktop is fine.

2. **`invalid_client` in browser does not mean the client is broken.** Always sanity-check with `curl` first:
   ```bash
   curl -sL -o /dev/null -w "HTTP %{http_code} → %{url_effective}\n" "<auth_url>"
   ```
   If curl gets `HTTP 200 → ...signin/identifier...`, the client is fine — it's a browser issue. Tell user to open in incognito.

3. **Test users must be added in the new Google Auth Platform UI** (Audience tab, not the old Credentials → OAuth consent screen). If "ineligible account" error on add, retry with lowercase or wait/refresh.

4. **State expires.** Each `start_google_auth` call returns a one-shot URL valid for ~5 minutes. Don't reuse old URLs from chat history.

5. **Don't suggest "publish to Production" lightly.** Drive (full) is a restricted scope — unverified Production may block the developer themselves. The 7-day Testing refresh limit is usually less friction than dealing with unverified Production restrictions or scope downgrades.

## When user says "google docs not working" — triage order

1. Run quick state check (top of file). If credentials JSON missing → setup not done, point to Obsidian note.
2. Check token expiry. If `expiry` in the past → Recipe 1 (re-auth).
3. If MCP not in `claude mcp list` → reregister with Recipe 5 base command.
4. If browser returns `invalid_client` during re-auth → curl-check the URL, then tell user to use incognito.
5. If browser returns 400 → likely Desktop client type instead of Web; see Trap 1.
6. If browser returns "Access blocked: not a test user" → add user email in Audience tab of GCP Console.

## File map

- `~/.config/google-workspace-mcp/client_secret.json` — OAuth client credentials (Web app)
- `~/.config/google-workspace-mcp/credentials/zeyka666@gmail.com.json` — refresh+access tokens
- `~/.config/google-workspace-mcp/reauth.sh` — one-shot re-auth helper
- `~/.claude.json` — MCP server registration (user scope, entry `google-workspace`)
- GCP project: `claude-mcp-workspace` (number `375915317046`), owner `Zeyka666@gmail.com`
- Full setup notes: `${OBSIDIAN_VAULT}/general/Knowledge/google-workspace-mcp.md`
