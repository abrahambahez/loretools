![loretools](loretools-banner.jpg)

Reference management library built for AI agents. Local-first, no GUI, no human workflows — clean functions an agent can call with confidence.

## install

**Primary: Claude Co-Work (recommended for researchers)**

See **[docs/getting-started.md](docs/getting-started.md)** for the full Co-Work setup guide. The short version: download a release zip from the [Releases page](https://github.com/abrahambahez/loretools/releases), upload it to your Co-Work session with the `loretools-manager` skill, and the agent handles the rest.

**Secondary: direct binary download (technical users)**

Download the binary for your platform from the [Releases page](https://github.com/abrahambahez/loretools/releases), unzip it, and place `lore` in your collection directory. Run it from that directory — no PATH installation required.

### install skills

macOS / Linux (default: English):

```bash
curl -fsSL https://raw.githubusercontent.com/abrahambahez/loretools/main/install-skills.sh | bash
```

Spanish skills:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/abrahambahez/loretools/main/install-skills.sh) --lang es
```

Windows (elevated PowerShell):

```powershell
irm https://raw.githubusercontent.com/abrahambahez/loretools/main/install-skills.ps1 | iex
```

To uninstall skills:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/abrahambahez/loretools/main/install-skills.sh) --uninstall
```

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/abrahambahez/loretools/main/install-skills.ps1))) -Uninstall
```

## config

Config is loaded from `.loretools/config.json` inside the **collection directory** (the directory where you run `lore`). Created automatically with defaults on first run.

```jsonc
{
  "backend": "local",

  // Where library.json, files/, and staging/ are stored.
  // Defaults to the collection directory (CWD). Change only if you want data
  // stored somewhere other than the collection folder itself.
  "local": {
    "library_dir": "/path/to/collection"
  },

  "apis": {
    // Recommended: identifies your requests to Crossref and OpenAlex,
    // unlocking polite-pool rate limits on both sources.
    "email": "you@example.com",

    // All six sources are enabled by default.
    // Set "enabled": false on any source you want to disable.
    // google_books also requires the GBOOKS_API_KEY env var to activate.
    "sources": [
      { "name": "crossref",         "enabled": true },
      { "name": "semantic_scholar", "enabled": true },
      { "name": "arxiv",            "enabled": true },
      { "name": "openalex",         "enabled": true },
      { "name": "doaj",             "enabled": true },
      { "name": "google_books",     "enabled": true }
    ]
  },

  // Optional. Model used for PDF extraction via Claude vision
  // (fallback when pdfplumber cannot extract selectable text).
  // Requires ANTHROPIC_API_KEY. Omit this block to use the default.
  "llm": {
    "model": "claude-sonnet-4-6"
  },

  // Optional. Controls how citekeys are generated at merge time.
  // Omit this block to use the defaults shown here.
  "citekey": {
    // Tokens: {author[N]} = first N surnames, {year} = 4-digit year.
    "pattern": "{author[2]}{year}",
    // Joins multiple author surnames (e.g. "smith_jones2021").
    "separator": "_",
    // Appended when authors exceed the N in {author[N]}.
    "etal": "_etal",
    // How to disambiguate identical keys: "letters" (a/b/c)
    // or "title[1-9]" (first N words of the title).
    "disambiguation_suffix": "letters"
  },

  // Optional. Required when sync is present — identifies this device.
  // peer_id = who you are (e.g. your name), device_id = this machine.
  "peer": {
    "peer_id": "alice",
    "device_id": "laptop"
  },

  // Optional. Enables S3-backed distributed sync across devices.
  // Works with AWS S3, Cloudflare R2, Backblaze B2, or MinIO.
  // endpoint: null targets AWS S3; set a URL for any other provider.
  // Omit this block entirely for local-only operation.
  "sync": {
    "bucket": "my-loretools-bucket",
    "access_key": "YOUR_ACCESS_KEY",
    "secret_key": "YOUR_SECRET_KEY",
    "endpoint": null
  }
}
```

API keys are never stored in config — set them as environment variables:

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | PDF metadata extraction via Claude vision (fallback when pdfplumber fails) |
| `GBOOKS_API_KEY` | Enables Google Books as a search/fetch source |
| `SEMANTIC_SCHOLAR_API_KEY` | Raises Semantic Scholar rate limits |

Without these keys features degrade gracefully: LLM extraction is skipped, Google Books is disabled.

## CLI

`lore` is a full command-line interface that mirrors every public API function. All commands output JSON envelopes for agent consumption.

```bash
# references
lore refs add '{"type":"article-journal","title":"...","author":[{"family":"Smith"}],"issued":{"date-parts":[[2020]]}}'
lore refs get --citekey vaswani2017
lore refs update vaswani2017 '{"note":"foundational"}'
lore refs rename vaswani2017 vaswani_etal2017
lore refs delete vaswani2017
lore refs list
lore refs filter --query attention --year 2017

# discover / fetch / extract
lore discover "transformer attention mechanism" --limit 5
lore fetch 10.48550/arXiv.1706.03762
lore extract papers/vaswani2017.pdf

# file archive
lore files attach vaswani2017 papers/vaswani2017.pdf
lore files detach vaswani2017
lore files get vaswani2017
lore files move vaswani2017 attention.pdf
lore files list
lore files reindex

# staging
lore staging stage '{"title":"..."}' --file papers/draft.pdf
lore staging list
lore staging delete draft2024
lore staging merge
lore staging merge --omit draft2024

# sync
lore sync push-changelog
lore sync pull-changelog
lore sync snapshot
lore sync conflicts
lore sync resolve <uid> title "Corrected Title"
lore sync restore vaswani2017
lore sync sync-file vaswani2017
lore sync unsync-file vaswani2017

# peers
lore peers init alice laptop
lore peers register-self
lore peers register alice '{"peer_id":"alice","device_id":"laptop","pubkey_hex":"..."}'
lore peers add-device bob '{"peer_id":"bob","device_id":"phone","pubkey_hex":"..."}'
lore peers revoke-device bob old-tablet
lore peers revoke bob
```

Every command exits 0 on success, 1 on error; JSON is always written to stdout.

## usage (Python API)

```python
import loretools

# discover references from external sources (Crossref, Semantic Scholar, arXiv, OpenAlex, DOAJ, Google Books)
result = loretools.discover_references("transformer attention mechanism", limit=5)

# fetch full record by DOI, arXiv ID, or ISSN
result = loretools.fetch_reference("10.48550/arXiv.1706.03762")

# extract metadata from a local PDF
result = loretools.extract_from_file("papers/vaswani2017.pdf")

# CRUD
loretools.add_reference({"type": "article-journal", "title": "Attention Is All You Need", ...})
loretools.get_reference("vaswani2017")
loretools.update_reference("vaswani2017", {"note": "foundational"})
loretools.rename_reference("vaswani2017", "vaswani_etal2017")
loretools.delete_reference("vaswani2017")
loretools.list_references(page=1)

# filter local library
loretools.filter_references(query="attention")               # title substring
loretools.filter_references(author="vaswani", year=2017)     # field predicates (ANDed)
loretools.filter_references(ref_type="book", has_file=True)  # type and file presence
loretools.filter_references(query="draft", staging=True)     # search staging store instead

# file archive
loretools.attach_file("vaswani2017", "papers/vaswani2017.pdf")
loretools.sync_file("vaswani2017")            # upload to S3
loretools.get_file("vaswani2017")             # resolve local or cached path
loretools.unsync_file("vaswani2017")          # clear blob_ref, keep local
loretools.detach_file("vaswani2017")          # remove local copy
loretools.move_file("vaswani2017", "attention.pdf")
loretools.list_files(page=1)
loretools.reindex_files()                     # repair stale paths after library move

# staging — review before committing to the library
loretools.stage_reference({"title": "..."}, file_path="papers/draft.pdf")
loretools.list_staged(page=1)
loretools.delete_staged("draft2024")
loretools.merge()                    # moves all staged refs into the main library
loretools.merge(omit=["draft2024"]) # skip specific citekeys
```

Every function returns a typed Result model — never raises.

## peer identity & distributed sync

```python
import loretools

# initialise a local peer identity (generates Ed25519 keypair)
loretools.peer_init(peer_id="alice", device_id="laptop")

# bootstrap admin on an empty peer directory (first-time setup)
loretools.peer_register_self()

# register another peer (requires admin role)
loretools.peer_register(peer_id="bob", pubkey_hex="<hex>")

# device lifecycle
loretools.peer_add_device(peer_id="bob", device_id="phone", pubkey_hex="<hex>")
loretools.peer_revoke_device(peer_id="bob", device_id="old-tablet")
loretools.peer_revoke(peer_id="bob")   # revoke entire peer
```

To enable sync, add `peer` and `sync` blocks to `config.json` (see [config](#config) above). Without a `sync` block the library runs local-only and the functions below are no-ops.

```python
# push local change log entries to remote backend
loretools.push_changelog()

# pull and replay remote entries (LWW per field, HLC causality)
loretools.pull_changelog()

# upload a snapshot for peer bootstrapping
loretools.create_snapshot()

# conflict management (concurrent field edits within 60 s window)
loretools.list_conflicts()
loretools.resolve_conflict(uid="sha256:abc", field="title", winning_value="Corrected Title")
loretools.restore_reference("vaswani2017")   # undo a remote delete
```

## search sources

Crossref · Semantic Scholar · arXiv · OpenAlex · DOAJ · Google Books — queried concurrently, results normalized to CSL-JSON. All sources retry up to 3 times with a 5s delay on rate limits or server errors.

## dev

```bash
uv sync
bash init.sh       # health check
uv run pytest      # full test suite
```
