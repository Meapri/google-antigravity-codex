# Security

Google Antigravity Codex is a local Codex plugin. It does not depend on Hermes,
`agy`, Gemini Web cookies, browser credential import, or macOS Keychain access.

## Credentials

Default credential files:

```text
~/.config/google-antigravity-codex/credentials.json
~/.config/google-antigravity-codex/oauth_client.json
```

Both files should be treated as secrets. The plugin writes credentials with
`0600` file permissions and avoids returning token values through MCP tools.

Configure the OAuth client with either:

```text
GOOGLE_ANTIGRAVITY_CLIENT_ID
GOOGLE_ANTIGRAVITY_CLIENT_SECRET
```

or an `oauth_client.json` file:

```json
{
  "client_id": "your-client-id.apps.googleusercontent.com",
  "client_secret": "your-client-secret"
}
```

## Network Behavior

Requests go to Google OAuth and Antigravity/Code Assist endpoints. The plugin
does not send requests through Hermes, `agy`, Gemini API key endpoints, or a
separate repair service.

## Integrated Helpers

The writing helper sends only the prompt, optional source text, optional local
project context, and style instructions to Antigravity. It does not read Gemini
Web cookies or browser profiles.

The release helper reads local git metadata, version files, and optional check
command output from the requested repository. It drafts release artifacts only;
it does not create tags, push tags, or publish GitHub releases.

## Reporting Issues

Include command names, sanitized errors, model IDs, and whether auth is present.
Never include raw credential files, OAuth tokens, refresh tokens, client
secrets, cookies, or authorization headers.
