# spec: 029-knowledge-layer-read — read and convert reference files for the knowledge layer

## findings

From docs/knowledge-layer-manifesto.md and the design session on 2026-04-17:

**Knowledge layer foundation:** The `read` operation is the entry point for the knowledge layer. It takes an archived reference file and produces a document ready for agent consumption — structural reading, entity reading, cross-reading. Output quality directly determines what knowledge layer operations are possible downstream.

**Extraction strategy (two-tier, local-only):**

1. **pymupdf4llm** (primary) — produces structured Markdown with headers, tables, and layout. Works correctly on text-native PDFs (embedded `fill-text`). Fails silently on scanned PDFs with embedded OCR layers (`ignore-text`): produces near-empty output with blank `## ` headers despite a successful exit. This is a false success and must be detected.

2. **pymupdf** via `page.get_text()` (fallback) — reads all text layers including embedded OCR (`ignore-text`). Produces flat, unstructured text. No false successes on any PDF type tested.

**Quality detection — the false success problem:**
pymupdf4llm cannot detect its own failure on OCR PDFs. Detection heuristics:
- `chars_per_page = total_text_chars / page_count` — below ~200 on a prose document signals failure
- `empty_header_ratio = empty_headers / total_headers` — high ratio (>0.5) on a multi-page document signals structural extraction failure

Both must be checked; a document with few headers (a letter, a dataset) must not be penalized by the second check alone. The `empty_header_ratio` penalty only applies when total headers ≥ 10.

**Output format as quality signal:**
- `.md` — pymupdf4llm succeeded; document has native structure
- `.txt` — pymupdf fallback was used; document is flat

Post-processing `.txt` into structured Markdown (font-size heuristics via `page.get_text("dict")`) is deferred to a future spec.

**No `agent_extraction_needed` in the knowledge layer.** The agent running loretools IS Claude — it reads files natively. The `read` operation returns a quality score; the agent decides what to do with low-quality output. The deprecated `agent_extraction_needed` concept belongs to the old extract.py design (ADR-002, superseded by this spec).

**extract.py is a separate concern.** It uses `pymupdf` directly for bibliographic metadata extraction from the first N pages. This spec does not touch it.

**Directory restructure:** The current `files/` directory serves only as a raw file store. The knowledge layer requires a parallel read output store. Both should live under a shared `sources/` root:
- `sources/raw/` — original files, replaces `files/`. Filename = citekey + original extension (e.g. `scott1990.pdf`)
- `sources/read/` — extracted content. Filename = citekey + format extension (e.g. `scott1990.md` or `scott1990.txt`)

This makes the relationship between raw and extracted objects explicit and navigable by citekey alone. `LocalSettings.files_dir` is renamed to `sources_raw_dir`; `sources_read_dir` is added as a new computed field. Both derive from `sources_dir = library_dir / "sources"`.

## objective

Restructure the sources directory, implement the `read` operation: convert an archived reference file into an agent-consumable document, detect and recover from extraction failures, and signal output quality via format and method metadata. Entirely local — no network, no API calls, no LLM inference.

## acceptance criteria (EARS format)

- when `read_reference(citekey, ctx)` is called on a reference with a linked PDF that is text-native, the system must use pymupdf4llm, pass quality checks, write `{citekey}.md` to `sources/read/`, and return `ReadResult(citekey, output_path, format="md", method="pymupdf4llm", quality_score≥0.4)`
- when `read_reference(citekey, ctx)` is called on a reference with a linked PDF where pymupdf4llm produces a false success (quality_score < 0.4), the system must fall back to pymupdf, write `{citekey}.txt` to `sources/read/`, and return `ReadResult(citekey, output_path, format="txt", method="pymupdf", quality_score<0.4)`
- when `read_reference(citekey, ctx)` is called on a reference with no linked file, the system must return `ReadResult(citekey, error="no file linked")` and never raise
- when `read_reference(citekey, ctx)` is called and the file does not exist on disk, the system must return `ReadResult(citekey, error="file not found: {path}")` and never raise
- when `read_references(citekeys, ctx)` is called with a list, the system must process all references concurrently via `asyncio.gather`, return `ReadBatchResult(results, total_read, total_failed)`, and never raise
- when a `ReadResult` is returned, `quality_score` must be a float between 0.0 and 1.0 and `format` must be one of `"md"` or `"txt"`
- when `read_reference` is called on an already-converted reference (output file exists), the system must return the existing result without re-converting unless `force=True` is passed
- when any file operation references a raw source file, the path must resolve under `sources/raw/`; when any file operation references extracted content, the path must resolve under `sources/read/`

## tasks

- [ ] task-01: restructure `sources/` directory in `LocalSettings` and update all references (blocks: none)
  - In `loretools/models.py`, replace `files_dir` computed field with three fields on `LocalSettings`:
    - `sources_dir: Path` → `library_dir / "sources"`
    - `sources_raw_dir: Path` → `sources_dir / "raw"`
    - `sources_read_dir: Path` → `sources_dir / "read"`
  - Update `LibraryCtx.files_dir` field to `sources_raw_dir`
  - Update all services, adapters, and CLI code that reference `files_dir` or `local.files_dir`
  - Update `_LOCAL_COMPUTED` in `config.py` to reflect renamed fields
  - tests: `LocalSettings` path derivation, no references to `files_dir` remain in core

- [ ] task-02: add `ReadResult`, `ReadBatchResult` models to `loretools/models.py` (blocks: task-01)
  - `ReadResult(citekey: str, output_path: str | None, format: Literal["md","txt"] | None, method: Literal["pymupdf4llm","pymupdf"] | None, quality_score: float | None, page_count: int | None, error: str | None)`
  - `ReadBatchResult(results: list[ReadResult], total_read: int, total_failed: int)`
  - All models `ConfigDict(extra="forbid")`
  - tests: field validation, quality_score bounds, Literal enforcement

- [ ] task-03: implement quality check function (blocks: task-02)
  - Create `loretools/services/read.py`: `_check_quality(text: str, page_count: int) -> float`
  - `chars_per_page = len(text) / max(page_count, 1)`
  - `empty_header_ratio`: count `## ` or `# ` lines with no following non-empty line within 2 lines; only apply when total headers ≥ 10
  - Return composite score: `min(chars_per_page / 500, 1.0) * (1.0 - empty_header_ratio * 0.5)`
  - Threshold: score < 0.4 → fallback required
  - tests: scott1990-like input (near-empty headers), anand2017-like input (rich structure), short doc with few headers (no header penalty), empty string

- [ ] task-04: implement pymupdf4llm conversion with quality gate (blocks: task-03)
  - In `loretools/services/read.py`: `async def _convert_with_pymupdf4llm(file_path: str, page_count: int) -> tuple[str, float]`
  - Call `pymupdf4llm.to_markdown(file_path)`; on any exception return `("", 0.0)`
  - Call `_check_quality(md, page_count)`; if score < 0.4 return `("", 0.0)`
  - Return `(md, score)` on success
  - tests: text-native PDF passes quality gate, OCR-layer PDF fails and returns empty

- [ ] task-05: implement pymupdf fallback conversion (blocks: task-03)
  - In `loretools/services/read.py`: `async def _convert_with_pymupdf(file_path: str) -> tuple[str, int]`
  - Open with `pymupdf.open()`, iterate all pages via `page.get_text()`
  - Assemble with `---\n[page {i}]\n\n{text}` separators; return `(assembled_text, page_count)`
  - On any exception return `("", 0)`
  - tests: OCR-layer PDF (scott1990 fixture), text-native PDF, corrupted/missing file

- [ ] task-06: implement `read_reference` and `read_references` (blocks: task-05)
  - `async def read_reference(citekey: str, ctx: LibraryCtx, force: bool = False) -> ReadResult`
    - Resolve file path from ctx under `sources_raw_dir`; return error result if missing
    - Check for existing output file in `sources_read_dir` unless `force=True`; return cached result if found
    - Get `page_count` via `pymupdf.open()`
    - Try `_convert_with_pymupdf4llm`; if score < 0.4 fall back to `_convert_with_pymupdf`
    - Write output to `ctx.sources_read_dir / f"{citekey}.md"` or `.txt`
    - Return `ReadResult` with `format`, `method`, `quality_score`, `page_count`, `output_path`
  - `async def read_references(citekeys: list[str], ctx: LibraryCtx, force: bool = False) -> ReadBatchResult`
    - Fan out via `asyncio.gather`; collect results and count failures
  - Sync wrappers in `loretools/__init__.py`
  - tests: text-native PDF end-to-end (.md output), OCR PDF end-to-end (.txt output), cache hit skips re-conversion, force=True re-converts, batch with mixed results

- [ ] task-07: update all tests that reference `files_dir` or `files/` path (blocks: task-01)
  - `tests/unit/test_config.py` — update path assertions from `files_dir` / `"files"` to `sources_raw_dir` / `"sources/raw"`
  - `tests/unit/test_local_adapter.py` — rename `files_dir` fixtures to `sources_raw_dir`; update directory paths
  - `tests/unit/test_files.py` — update `make_ctx` helper and all `files_dir` references to `sources_raw_dir`
  - `tests/unit/cli/test_files.py` — same as above
  - `tests/unit/test_merge_service.py`, `test_staging_service.py`, `test_store.py`, `test_extract.py`, `test_filter.py` — update any `files/` path fixtures
  - `tests/integration/test_staging_workflow.py` — update directory assertions
  - Run full test suite (`uv run pytest`) and confirm green before proceeding

- [ ] task-08: update user-facing documentation and templates (blocks: task-01)
  - `docs/product.md` lines 56, 80 — replace `~/.loretools/files/` with `~/.loretools/sources/raw/`; add mention of `sources/read/` as extracted content store
  - `docs/getting-started.md` lines 14, 83, 96 — update directory tree and config table; replace `files/` with `sources/raw/`
  - `docs/structure.md` — no direct `files/` references but add `sources/` layout to the directory diagram if it shows the data directory
  - `README.md` line 29 — update comment showing directory layout
  - `templates/en/init-prompt.md` line 48 — update directory tree
  - `templates/es/init-prompt.md` — same as English template
  - `skills/en/loretools-references/SKILL.md` lines 64, 73, 81 — update `files/` references to `sources/raw/`
  - `skills/es/loretools-references/SKILL.md` — same as English skill

- [ ] task-09: update CHANGELOG and supersede ADR-002 (blocks: task-08)
  - Add CHANGELOG entry under `[Unreleased]`; mark `sources/` rename as breaking change
  - Update `docs/adr/002-pdf-extraction.md` status to `Superseded by spec 029`
  - Remove `loretools-llm plugin` reference from `loretools/cli/__init__.py`

## ADR required?

No new ADR. Spec 029 supersedes ADR-002. Design decisions are captured in the findings section above.

## risks

- **Quality thresholds need calibration.** The 0.4 score threshold and 500 chars/page divisor are derived from two test cases (scott1990, anand2017). Validate against a broader sample before treating them as stable. Consider exposing the threshold via `Settings`.
- **`sources/` rename is a breaking change for existing libraries.** Users with data under `files/` will need a migration step. This spec does not include a migration; it should be documented in the CHANGELOG as a breaking change.
- **pymupdf4llm may fix its OCR layer handling.** The quality gate is a workaround for a known library bug. If fixed upstream, the gate remains correct but redundant.
