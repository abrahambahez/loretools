---
name: loretools-references
description: loretools reference management — extract metadata from local PDFs, stage candidates, merge into the library, perform full CRUD on library records, and manage files attached to references (attach, detach, move, list). Use this for any loretools task involving extracting references from PDFs, adding them to the library, filtering or searching the library, updating or deleting records, the full staging→merge workflow, or attaching/removing PDFs and EPUBs. If the user is doing anything research-related with loretools that isn't purely about setup, use this skill.
---

## Concepts

- **Staging**: exploration scratchpad. References live here until promoted.
- **Library**: production store. Every record has a citekey assigned at merge.
- **Typical flow**: `lore extract <pdf>` → `lore staging stage` → review → `lore staging merge`

## Extract

```sh
lore extract <file_path>
# Extracts metadata from a local PDF using pdfplumber.
# If extraction confidence is low, returns agent_extraction_needed: true —
# the agent should then read the PDF directly and build the JSON manually.
```

## Staging

```sh
lore staging stage '<json>' [--file <path>]
echo '<json>' | lore staging stage              # from stdin

lore staging list-staged [--page N]

lore staging delete-staged <citekey>

lore staging merge [--omit key1,key2,...] [--allow-semantic]
# --allow-semantic: also promote records with uid_confidence=="semantic"
```

## Library CRUD

```sh
lore refs add '<json>'
echo '<json>' | lore refs add                   # from stdin

lore refs get <citekey> [--uid <uid>]

lore refs update <citekey> '<json>'
echo '<json>' | lore refs update <citekey>      # from stdin

lore refs rename <old_key> <new_key>

lore refs delete <citekey>

lore refs list [--page N]

lore refs filter [--query "<text>"] [--author "<surname>"] [--year YYYY] \
                 [--type <csl-type>] [--has-file] [--staging] [--page N]
# --type examples: article-journal, book, chapter
# --staging: filter staged records instead of library
```

## Files

Files are attached to **library** references (not staged ones). Each reference holds at most one file.

```sh
lore files attach <citekey> <path>
# Copies <path> to sources/raw/ and registers it on the reference.

lore files detach <citekey>
# Deletes the local copy and clears the file link.

lore files move <citekey> <dest_name>
# Renames the archived file. dest_name is filename only, no path.

lore files reindex
# Repairs stale paths if sources/raw/ was manually reorganized.

lore files get <citekey>
# Returns the absolute path to the local file.

lore files list [--page N]
```

To attach a file at intake: `lore staging stage '<json>' --file <path>` — `merge` moves it to `sources/raw/`.

## Key model fields

**ReferenceRow** (list/filter results): `citekey, title, authors, year, doi, uid, has_file, has_warnings`

**Reference** (full record): `id` (=citekey), `type` (CSL), `title`, `author: [{family, given}]`,
`issued: {date-parts: [[YYYY]]}`, `DOI`, `URL`, `uid`, `uid_confidence` ("authoritative"|"semantic")

**FileRow** (files list results): `citekey, path, mime_type, size_bytes`

**FileRecord** (on Reference as `_file`): `path, mime_type, size_bytes, added_at`
