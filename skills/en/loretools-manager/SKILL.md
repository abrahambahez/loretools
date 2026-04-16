---
name: loretools-manager
description: loretools collection manager — first-time setup in Claude Co-Work, binary installation, config creation, and session-start verification. Use this when the user wants to set up loretools for the first time, install the binary into a collection directory, create or update config.json, verify that a collection is operational, or when any loretools command fails because the binary or config is missing.
---

A **collection** is a directory that contains `lore`, `.lore/config.json`, and the researcher's library data. `lore` always operates relative to the current working directory (CWD) — no global config, no PATH installation needed.

## First-time setup (Claude Co-Work)

**Step 1 — Install the binary**

The researcher has uploaded a release zip. Unzip it and make it executable:

```bash
unzip lore-*.zip
chmod +x lore
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

**Step 3 — Apply user preferences (optional)**

If the user wants to customize citekey generation, edit `.lore/config.json`:

```json
{
  "citekey": { "pattern": "{author[1]}{year}" }
}
```

**Step 4 — Verify collection**

```bash
./lore refs list
./lore staging list-staged
```

Both should return `{"ok": true, ...}`. The collection is ready.

## Collection directory layout after setup

```
<collection>/
  lore                          # binary
  .lore/
    config.json                 # config (CWD-relative, auto-created)
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

| Field | Default | Description |
|-------|---------|-------------|
| `local.library_dir` | CWD | Root for all data files. Defaults to the collection directory. |
| `citekey.pattern` | `"{author[2]}{year}"` | Citekey generation pattern. |
| `citekey.separator` | `"_"` | Separator between author tokens. |
| `citekey.etal` | `"_etal"` | Suffix appended when authors exceed the pattern limit. |
| `citekey.disambiguation_suffix` | `"letters"` | `"letters"` (a/b/c) or `"title[1-9]"` (first N title words). |

## Citekey pattern tokens

- `{author[N]}` — first N author surnames joined by `separator`
- `{year}` — 4-digit year

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
