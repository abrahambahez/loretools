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
  // Where library.json, files/, and staging/ are stored.
  // Defaults to the collection directory (CWD). Change only if you want data
  // stored somewhere other than the collection folder itself.
  "local": {
    "library_dir": "/path/to/collection"
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
  }
}
```

## CLI

`lore` is a full command-line interface that mirrors every public API function. All commands output JSON envelopes for agent consumption.

```bash
# references
lore refs add '{"type":"article-journal","title":"...","author":[{"family":"Smith"}],"issued":{"date-parts":[[2020]]}}'
lore refs get vaswani2017
lore refs update vaswani2017 '{"note":"foundational"}'
lore refs rename vaswani2017 vaswani_etal2017
lore refs delete vaswani2017
lore refs list
lore refs filter --query attention --year 2017

# extract metadata from a local PDF
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
lore staging list-staged
lore staging delete-staged draft2024
lore staging merge
lore staging merge --omit draft2024
```

Every command exits 0 on success, 1 on error; JSON is always written to stdout.

## usage (Python API)

```python
import loretools

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
loretools.get_file("vaswani2017")
loretools.detach_file("vaswani2017")
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

## dev

```bash
uv sync
bash init.sh       # health check
uv run pytest      # full test suite
```
