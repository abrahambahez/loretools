# Claude Desktop Setup

Connect scholartools to Claude Desktop via the MCP server (`scht-mcp`).

## Config

Open `claude_desktop_config.json` and add the `mcpServers` block.

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux:** `~/.config/claude/claude_desktop_config.json`

### Production (uvx)

```json
{
  "mcpServers": {
    "scholartools": {
      "command": "uvx",
      "args": ["--from", "scholartools", "scht-mcp"]
    }
  }
}
```

### Local dev (uv run)

```json
{
  "mcpServers": {
    "scholartools": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/scholartools", "scht-mcp"]
    }
  }
}
```

Replace `/path/to/scholartools` with the absolute path to your local clone.

## Environment variables

Set these in `~/.zshrc` or `~/.bash_profile` so Claude Desktop inherits them.

| Variable | Required | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | LLM fallback in `ingest_file` |
| `SEMANTIC_SCHOLAR_API_KEY` | No | Higher rate limits on Semantic Scholar |
| `GBOOKS_API_KEY` | No | Enables Google Books source |

## Quick-start

1. Add the config block above and save the file.
2. Restart Claude Desktop.
3. Send: "use the discover tool to find papers about machine learning"

If you see staged references returned, the server is working.

## Troubleshooting

**stdio not found** — `uvx` or `uv` is not on the PATH that Claude Desktop sees. Add the binary location to `PATH` in `~/.zshrc` or `~/.bash_profile`, then restart Claude Desktop (not just the terminal).

**Config not picked up** — Confirm the file is at the correct path for your OS (see above). JSON must be valid — a trailing comma or missing brace will silently fail.

**Env vars not resolved** — Claude Desktop inherits env from the shell that launched it. Variables set only in the current terminal session (e.g. `export KEY=...` without adding to a profile file) will not be visible. Add them to `~/.zshrc` or `~/.bash_profile` and restart Claude Desktop.
