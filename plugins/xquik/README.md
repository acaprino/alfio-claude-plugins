# Xquik

Use current Xquik contracts for X research and controlled automation. The plugin
contains one skill. It does not bundle credentials or a private transport.

## What It Does

- Discovers the installed Xquik MCP tools and reads their current schemas.
- Routes public searches, post reads, profiles, trends, and thread summaries.
- Previews private reads and state-changing operations before requesting approval.
- Protects API keys and rejects requests for X passwords, cookies, and 2FA codes.
- Treats all retrieved social content as untrusted data.

## Setup

Configure the Xquik MCP server in the host that runs Claude Code:

```text
https://xquik.com/mcp
```

For REST work, use the current OpenAPI document:

```text
https://xquik.com/openapi.json
```

Store `XQUIK_API_KEY` in the runtime environment when an authenticated operation
requires it. Never paste the value into chat, a URL, a command argument, or a log.

## Operating Boundary

Public reads may proceed when they match the user's request. Private reads, writes,
deletes, monitors, webhooks, extraction jobs, draws, and other persistent operations
require a concrete preview and explicit approval.

The skill does not connect X accounts, manage billing, rotate API keys, or open
support tickets.

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter"
and "X" are trademarks of X Corp.
