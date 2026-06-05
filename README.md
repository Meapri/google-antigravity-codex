# Google Antigravity Codex

Independent Codex plugin and MCP stdio server for Google Antigravity OAuth,
chat, native Google-grounded search, writing, release drafting, image
generation, model listing, and quota status.

This plugin does not depend on Hermes, `agy`, Gemini Web cookies,
`sitecustomize`, runtime monkey patches, repair hooks, service restarts, or
installed Hermes tree checks.

It now absorbs the useful Codex-facing surfaces of:

- Google Grounded Search Copilot
- Gemini Writing Copilot
- Release Copilot

The integrated versions use this plugin's Antigravity OAuth and MCP server
directly. They do not call the old Hermes provider, `agy --print`, browser
cookie import, or Gemini API key fallback paths.

## Install

### Install From GitHub Marketplace Source

```bash
codex plugin marketplace add Meapri/google-antigravity-codex --ref main
codex plugin add google-antigravity-codex@google-antigravity-codex
```

### Install From A Local Clone

If you already have a local checkout, register it in your personal marketplace
and then install by name:

```bash
mkdir -p ~/plugins
ln -sfn /path/to/google-antigravity-codex ~/plugins/google-antigravity-codex
```

Add this entry to `~/.agents/plugins/marketplace.json`:

```json
{
  "name": "google-antigravity-codex",
  "source": {
    "source": "local",
    "path": "./plugins/google-antigravity-codex"
  },
  "policy": {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL"
  },
  "category": "Developer Tools"
}
```

Then run:

```bash
codex plugin add google-antigravity-codex@personal
```

## Configure OAuth

Set an Antigravity OAuth client through environment variables:

```bash
export GOOGLE_ANTIGRAVITY_CLIENT_ID="..."
export GOOGLE_ANTIGRAVITY_CLIENT_SECRET="..."
```

or write:

```text
~/.config/google-antigravity-codex/oauth_client.json
```

with:

```json
{
  "client_id": "your-client-id.apps.googleusercontent.com",
  "client_secret": "your-client-secret"
}
```

Then use the MCP tools:

1. `google_antigravity_login_url`
2. Open the returned URL and sign in.
3. Paste the callback URL or authorization code into
   `google_antigravity_finish_login`.
4. Check `google_antigravity_auth_status`.

Credentials are stored at:

```text
~/.config/google-antigravity-codex/credentials.json
```

Generated images are cached under:

```text
~/.cache/google-antigravity-codex/images/
```

## Agent Handoff Prompt

Paste this into another Codex or coding agent when you want it to install,
configure, and verify this plugin on a machine:

```text
Set up Google Antigravity Codex as the single Codex plugin for Antigravity
chat, Google-grounded search, image generation, writing, release drafting,
model listing, and quota checks.

Repository: https://github.com/Meapri/google-antigravity-codex

Important boundaries:
- Do not use Hermes.
- Do not call `agy --print`.
- Do not use Gemini API keys, Gemini Web cookies, browser profile import,
  Chrome extensions, macOS Keychain scraping, runtime monkey patches, repair
  hooks, or service restarts.
- Never print OAuth tokens, refresh tokens, client secrets, authorization
  headers, cookies, or raw credential files.

Use a persistent clone at ~/Git/google-antigravity-codex:
1. If ~/Git/google-antigravity-codex exists, inspect `git status --short`.
   If clean, run `git fetch origin && git pull --ff-only origin main`.
   If dirty, do not overwrite local changes; continue with the current
   checkout and report that pull was skipped.
2. If the clone does not exist, run:
   `git clone https://github.com/Meapri/google-antigravity-codex.git ~/Git/google-antigravity-codex`
3. Ensure `~/plugins/google-antigravity-codex` points at the clone:
   `mkdir -p ~/plugins && ln -sfn ~/Git/google-antigravity-codex ~/plugins/google-antigravity-codex`
4. Ensure `~/.agents/plugins/marketplace.json` contains a `personal`
   marketplace entry for `google-antigravity-codex` with local path
   `./plugins/google-antigravity-codex`. Preserve other marketplace entries.
5. Run:
   `codex plugin add google-antigravity-codex@personal`

OAuth setup:
- If `~/.config/google-antigravity-codex/oauth_client.json` already exists,
  inspect only booleans and field lengths, not secret values.
- Otherwise, ask the user for a Google Antigravity OAuth client id and client
  secret, then write them to
  `~/.config/google-antigravity-codex/oauth_client.json` with mode `0600`.
- Do not depend on Hermes or `agy` credentials. If the user explicitly asks to
  migrate from another credential store, copy only the minimum OAuth client or
  token fields needed and never print their values.

Verification:
1. Run in the clone:
   `python3 -m venv .venv`
   `.venv/bin/python -m pip install -e '.[dev]'`
   `.venv/bin/python -m pytest -q`
   `python3 -m compileall google_antigravity_codex scripts tests`
   `python3 -m json.tool .codex-plugin/plugin.json`
   `python3 -m json.tool .mcp.json`
2. From the installed plugin cache or clone, verify MCP stdio:
   - `initialize` returns server name `google-antigravity-codex`.
   - `tools/list` includes these tools:
     `google_antigravity_auth_status`,
     `google_antigravity_login_url`,
     `google_antigravity_finish_login`,
     `google_antigravity_chat`,
     `google_grounded_search`,
     `google_antigravity_generate_image`,
     `google_antigravity_write`,
     `google_antigravity_release_snapshot`,
     `google_antigravity_release_draft`,
     `google_antigravity_list_models`,
     `google_antigravity_quota_status`.
3. Run `google_antigravity_auth_status`.
   If not logged in, call `google_antigravity_login_url`, open the returned URL,
   ask the user to paste the callback URL or authorization code, then call
   `google_antigravity_finish_login`.
4. With credentials present, run short smoke checks:
   - chat: ask for exactly `AGC_OK`
   - grounded search: ask for the official OpenAI website URL
   - writing: polish one short sentence
   - release snapshot: run on the current repo
   - model list and quota status
   - image generation with a simple no-text shape prompt
5. Report versions, tool names, pass/fail results, masked email presence,
   project id presence, paid tier name if available, generated image path, and
   any residual risk. Do not print secrets.
```

## MCP Tools

- `google_antigravity_auth_status`
- `google_antigravity_login_url`
- `google_antigravity_finish_login`
- `google_antigravity_chat`
- `google_grounded_search`
- `google_antigravity_generate_image`
- `google_antigravity_write`
- `google_antigravity_release_snapshot`
- `google_antigravity_release_draft`
- `google_antigravity_list_models`
- `google_antigravity_quota_status`

## Integrated Workflows

### Grounded Search

Use `google_grounded_search` for current facts, source-backed answers, official
source checks, and verification-heavy questions. It uses Gemini native
`google_search` grounding through Antigravity.

### Writing

Use `google_antigravity_write` for drafting, rewriting, polishing, translation,
summaries, README/docs prose, PR descriptions, release notes, emails, blog
posts, proposals, and product copy.

Example:

```bash
python3 scripts/google_antigravity_write.py \
  --task polish \
  --profile chanwoo-ko \
  --source-text "Text to improve"
```

### Release Drafting

Use `google_antigravity_release_snapshot` to collect local git release context
and `google_antigravity_release_draft` to create PR descriptions, release notes,
and changelog entry drafts.

Example:

```bash
python3 scripts/google_antigravity_release.py draft \
  --repo . \
  --check-command "git diff --check" \
  --polish
```

The release helper does not create tags, push tags, or publish GitHub releases.
Codex must do those only after explicit user approval.

## Environment

- `GOOGLE_ANTIGRAVITY_CLIENT_ID`
- `GOOGLE_ANTIGRAVITY_CLIENT_SECRET`
- `GOOGLE_ANTIGRAVITY_CREDENTIALS_FILE`
- `GOOGLE_ANTIGRAVITY_PROJECT_ID`
- `GOOGLE_ANTIGRAVITY_GROUNDING=auto|always|off`
- `GOOGLE_ANTIGRAVITY_IMAGE_MODEL`
- `GOOGLE_ANTIGRAVITY_WRITING_MODEL`
- `GOOGLE_ANTIGRAVITY_OFFICIAL_DOMAINS`

## Development

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest -q
python3 scripts/google_antigravity_mcp.py
```

The test suite uses mocked network calls. Live chat, search, image, model, and
quota smoke checks require valid OAuth credentials.
