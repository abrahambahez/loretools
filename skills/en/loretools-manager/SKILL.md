---
name: loretools-manager
description: loretools collection manager — first-time setup in Claude Co-Work, binary installation, config creation, and session-start verification. Use this when the user wants to set up loretools for the first time, install the binary into a collection directory, create or update config.json, verify that a collection is operational, or when any loretools command fails because the binary or config is missing.
---

A **collection** is a directory that contains `lore`, `.lore/config.json`, and the researcher's library data. `lore` always operates relative to the current working directory (CWD) — no global config, no PATH installation needed.

## First-time setup (Claude Co-Work)

**Step 1 — Install the binary**

The researcher has uploaded a release zip. Unzip it and make it executable:

```bash
unzip scht-*.zip
chmod +x scht
```

Verify it works:

```bash
./lore --version
```

**Step 2 — Create config**

Run `lore` once from the collection directory to auto-create `.lore/config.json` with defaults:

```bash
./lore refs list
```

This creates `.lore/config.json` with `library_dir` set to the collection directory (CWD). No further path configuration is needed unless the user wants a non-default layout.

**Step 3 — Apply user preferences**

If the user provides API keys or wants to customize config, edit `.lore/config.json`. Common fields:

```json
{
  "apis": { "email": "you@example.com" },
  "llm": { "model": "claude-sonnet-4-6" }
}
```

Set API keys as environment variables (never in config):

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | PDF extraction via Claude vision |
| `GBOOKS_API_KEY` | Google Books source |

**Step 4 — Verify collection**

```bash
./lore refs list
./lore staging list
```

Both should return `{"ok": true, ...}`. The collection is ready.

## Collection directory layout after setup

```
<collection>/
  lore                          # binary
  .lore/
    config.json                 # config (CWD-relative, auto-created)
    keys/                       # Ed25519 keypairs (sync only)
  library.json                  # production library (created on first add/merge)
  files/                        # archived PDF/document files
  staging.json                  # staged references
  staging/                      # staged files
```

## Subsequent-session verification

At the start of each Co-Work session, verify the collection is accessible:

```bash
./lore --version
./lore refs list
```

If `lore` is not found, the binary was not uploaded or the working directory is wrong. Ask the user to confirm the folder is mounted and `lore` is present.

## Config reference

All fields except `backend` and `local` are optional.

| Field | Default | Description |
|-------|---------|-------------|
| `backend` | `"local"` | Storage backend. Always `"local"` unless using S3 sync. |
| `local.library_dir` | CWD | Root for all data files. Defaults to the collection directory. |
| `apis.email` | (none) | Identifies requests to Crossref/OpenAlex for polite-pool rate limits. |
| `llm.model` | `"claude-sonnet-4-6"` | Claude model for PDF vision extraction. |
| `citekey.pattern` | `"{author[2]}{year}"` | Citekey generation pattern. |

## Citekey pattern tokens

- `{author[N]}` — first N author surnames joined by `separator`
- `{year}` — 4-digit year
- `etal` — appended when authors exceed N
- `disambiguation_suffix`: `"letters"` (a/b/c) or `"title[1-9]"` (first N title words)

## Global flag

```
./lore --plain <command>   # human-readable table output instead of JSON
```

## Computed paths (relative to library_dir)

| Path | Purpose |
|------|---------|
| `library.json` | Production library |
| `files/` | Archived files |
| `staging.json` | Staged references |
| `staging/` | Staged files |
| `peers/` | Peer registry (sync only) |
