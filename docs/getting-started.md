# Getting started with loretools

This guide is for researchers using **Claude Co-Work** (Claude's Projects with file access). No terminal experience required — your AI agent handles all shell operations.

---

## What is a collection?

A **collection** is a single folder that contains everything loretools needs:

- `lore` — the binary the agent runs
- `.lore/config.json` — your preferences and settings
- `library.json` — your reference library
- `files/` — PDF and document files linked to references
- `staging/` — references waiting to be reviewed and merged

You create one collection per research project (or one shared collection across projects — your choice).

---

## First session: setting up your collection

### 1. Download the release zip

Go to the [Releases page](https://github.com/abrahambahez/loretools/releases) and download the zip for your platform:

- **macOS (Apple Silicon):** `scht-X.Y.Z-macos-arm64.zip`
- **Linux:** `scht-X.Y.Z-linux-x86_64.zip`
- **Windows:** `scht-X.Y.Z-windows-x86_64.zip`

### 2. Prepare your collection folder

Create or choose a folder for your research collection. This folder will hold all your references and files — keep it in a place that persists between sessions (e.g. your Documents folder, not a temporary upload area).

### 3. Open Claude Co-Work and mount your collection folder

Open Claude Projects and connect your collection folder so the agent can read and write files there.

### 4. Upload the release zip

Upload the zip file you downloaded in step 1 to your Co-Work session.

### 5. Install the `loretools-manager` skill

Download the skill zip from the same Releases page (`loretools-loretools-manager-en-X.Y.Z.zip` for English or the `es` variant for Spanish) and install it. Ask the agent:

> "Please install the loretools-manager skill from this zip."

### 6. Ask the agent to complete setup

Once the skill is installed, say:

> "Set up loretools in my collection folder."

The agent will:
1. Unzip `lore` and make it executable
2. Run it once to auto-create `.lore/config.json`
3. Verify the collection is operational

### 7. Verify everything works

Ask the agent:

> "List my references."

You should see a response like `{"ok": true, "references": [], ...}`. Your collection is ready.

---

## Subsequent sessions

Each time you open a new Co-Work session:

1. Open Claude Projects and mount your collection folder
2. Ask the agent to verify the collection:

   > "Verify that loretools is working."

   The agent checks that `lore` is present and the config is valid.

3. Start working — add references, fetch metadata, merge staged items, etc.

---

## Collection directory layout

After setup your collection folder looks like this:

```
<your-collection>/
  lore                          # the loretools binary
  .lore/
    config.json                 # settings (auto-created on first run)
    keys/                       # Ed25519 keypairs (only if using sync)
  library.json                  # your reference library
  files/                        # archived PDFs and documents
  staging.json                  # staged references
  staging/                      # staged files
```

The agent always runs `lore` from this folder, so all paths resolve correctly without any PATH configuration.

---

## Config reference

`.lore/config.json` is created automatically with sensible defaults. You only need to edit it if you want to change something.

| Field | Default | What it controls |
|-------|---------|-----------------|
| `backend` | `"local"` | Storage backend. Leave as `"local"` for Co-Work use. |
| `local.library_dir` | Collection folder (CWD) | Where `library.json`, `files/`, and `staging/` are stored. The default — the collection folder itself — is correct for Co-Work. |
| `apis.email` | (none) | Your email for Crossref and OpenAlex polite-pool rate limits. Recommended. |
| `llm.model` | `"claude-sonnet-4-6"` | Claude model for PDF text extraction (scanned PDFs). Requires `ANTHROPIC_API_KEY`. |
| `citekey.pattern` | `"{author[2]}{year}"` | Pattern for generated reference keys. |

### API keys

API keys are never stored in `config.json`. Set them as environment variables in your Co-Work session:

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | PDF extraction via Claude vision (scanned PDFs) |
| `GBOOKS_API_KEY` | Google Books as a search source |
| `SEMANTIC_SCHOLAR_API_KEY` | Higher Semantic Scholar rate limits |

Without these keys the tool degrades gracefully: LLM extraction is skipped, Google Books is disabled.

---

## Troubleshooting

**`lore` not found after upload**
Make sure the zip was unzipped and the resulting file is named `lore` (not `scht-X.Y.Z-platform`). Ask the agent: "List files in the collection folder."

**Permission denied when running `lore`**
The binary needs execute permission. Ask the agent: "Make lore executable with chmod +x."

**Config not found or incomplete**
Run `./lore refs list` once — this auto-creates `.lore/config.json` if it's missing.

**Library operations fail on first use**
`library.json` and `staging.json` are created automatically on first write (first `merge` or `add`). Empty list results before that are normal.
