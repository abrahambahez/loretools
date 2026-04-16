---
name: loretools-references
description: loretools reference management — discover references from external APIs, fetch by DOI/arXiv/ISBN, extract metadata from local PDFs, stage candidates, merge into the library, perform full CRUD on library records, and manage files attached to references (link, unlink, move, list). Use this for any loretools task involving finding references, adding them to the library, filtering or searching the library, updating or deleting records, the full staging→merge workflow, or attaching/removing PDFs and EPUBs. If the user is doing anything research-related with loretools that isn't purely about sync, use this skill.
---

## Concepts

- **Staging**: exploration scratchpad. References live here until promoted.
- **Library**: production store. Every record has a citekey assigned at merge.
- **Typical flow**: discover/fetch/extract → `lore staging stage` → review → `lore staging merge`

## Discovery

```sh
lore discover "<query>" [--sources crossref,semantic_scholar,...] [--limit N]
# sources: crossref, semantic_scholar, arxiv, openalex, doaj, google_books

lore fetch <identifier>
# identifier: DOI, arXiv ID, or ISBN

lore extract <file_path>
# Requires ANTHROPIC_API_KEY for LLM fallback on scanned PDFs
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

Files are linked to **library** references (not staged ones). Each reference holds at most one file.

```sh
lore files link <citekey> <path>
# Copies <path> into the archive and links it to the reference.

lore files unlink <citekey>
# Removes the archive copy and clears the file link.

lore files move <citekey> <dest_name>
# Renames the archived file. dest_name is filename only, no path.

lore files list [--page N]
```

To attach a file at intake: `lore staging stage '<json>' --file <path>` — `merge` moves it to the archive.

## Key model fields

**ReferenceRow** (list/filter results): `citekey, title, authors, year, doi, uid, has_file, has_warnings`

**Reference** (full record): `id` (=citekey), `type` (CSL), `title`, `author: [{family, given}]`,
`issued: {date-parts: [[YYYY]]}`, `DOI`, `URL`, `uid`, `uid_confidence` ("authoritative"|"semantic")

**FileRow** (files list results): `citekey, path, mime_type, size_bytes`

**FileRecord** (on Reference as `_file`): `path, mime_type, size_bytes, added_at`
