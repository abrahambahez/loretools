# spec: 027-core-only-refactor — strip non-core modules, enforce portability invariant

## findings

From CHANGELOG analysis against docs/product.md and docs/tech.md:

**Problem:** The core package (`loretools/`) contains search adapters (httpx), LLM extraction (anthropic SDK), distributed sync infrastructure (HLC, change log, S3/MinIO via minio), and peer management (cryptography). All of these violate the portability invariant: *if a module imports httpx, anthropic, minio, or cryptography, it belongs in a plugin, not core.*

**Concrete violations:**

| Module | Network/auth import | Destination |
|---|---|---|
| `apis/` (7 files) | `httpx`, `anthropic` | future `loretools-search` / `loretools-llm` plugins |
| `services/search.py` | via `apis/` | future `loretools-search` plugin |
| `services/fetch.py` | via `apis/` | future `loretools-search` plugin |
| `services/blobs.py` | blob SHA utilities | future `loretools-sync` plugin |
| `services/hlc.py` | HLC timestamps | future `loretools-sync` plugin |
| `services/peers.py` | `cryptography` | future `loretools-sync` plugin |
| `services/sync.py` | `minio` via adapters | future `loretools-sync` plugin |
| `adapters/s3_sync.py` | `minio` | future `loretools-sync` plugin |
| `adapters/sync_composite.py` | change log | future `loretools-sync` plugin |
| `adapters/conflicts_store.py` | conflict store | future `loretools-sync` plugin |
| `adapters/peer_directory.py` | peer directory | future `loretools-sync` plugin |

**Local ops trapped in sync.py:** `attach_file`, `detach_file`, and the local path of `get_file` are purely local (no S3, no HLC, no change log). They must be salvaged into `services/files.py` before `sync.py` is deleted.

**LLM fallback in extract:** `services/extract.py` is clean (pdfplumber only). The LLM fallback was wired in `__init__.py` via `make_llm_extractor`. Since the toolkit targets agents with native vision, the correct behavior when pdfplumber fails is to return `agent_extraction_needed: True` with the file path — not to call the API.

**pyproject.toml violations:** `httpx[socks]`, `anthropic`, `cryptography` are core dependencies; `minio` is an optional dep. All must be removed.

## objective

Delete all non-core modules, salvage the three local file operations from `sync.py` into `files.py`, update models/ports/config/`__init__` to remove non-core surface, strip non-core dependencies from `pyproject.toml`, and run the test suite green. After this spec is complete, the core package has zero network/auth dependencies, all unit tests pass without credentials, and the only dependencies are `pydantic` and `pdfplumber`.

## acceptance criteria (EARS format)

- when `grep -r "import httpx\|import anthropic\|import minio\|import cryptography\|from cryptography\|from minio"` is run on `loretools/`, it must return zero matches
- when `uv run pytest tests/unit/` is run with no environment variables set, all tests must pass
- when `pyproject.toml` dependencies are inspected, the only runtime dependencies must be `pydantic>=2.0` and `pdfplumber>=0.11`
- when `extract_from_file()` is called on a PDF where pdfplumber yields no usable metadata, the system must return `ExtractResult(agent_extraction_needed=True, file_path=<path>)` rather than calling any external API
- when `attach_file(citekey, path)` is called, the system must copy the file to `files/` and register `FileRecord` — with no S3, no change log, and no HLC dependency
- when `detach_file(citekey)` is called, the system must delete the local copy and clear `_file` — with no S3 or change log dependency
- when `get_file(citekey)` is called, the system must return the local `files/` path — with no S3 or blob cache lookup
- when `lore files attach`, `lore files detach`, and `lore files get` are called, the CLI must route to the local-only implementations
- when `LibraryCtx` is inspected, it must contain no fields for `api_sources`, `llm_extract`, `peers_dir`, `data_dir`, `peer_id`, `device_id`, or `sync_config`
- when `Settings` is loaded from `.loretools/config.json`, it must parse only `local` and `citekey` blocks — `apis`, `llm`, `sync`, and `peer` blocks must not exist

## tasks

- [ ] task-01: delete non-core source modules (blocks: none)
  - Delete `loretools/apis/` (entire directory)
  - Delete `loretools/adapters/conflicts_store.py`, `peer_directory.py`, `s3_sync.py`, `sync_composite.py`
  - Delete `loretools/services/search.py`, `fetch.py`, `blobs.py`, `hlc.py`, `peers.py`, `sync.py`
  - Delete `loretools/cli/discover.py`, `fetch.py`, `peers.py`, `sync.py`

- [ ] task-02: delete non-core tests (blocks: task-01)
  - Delete all unit and integration tests for the deleted modules (22 files total)
  - Keep: `test_staging_workflow.py`, `test_file_management.py`, `test_file_progressive_enhancement.py` — verify none have sync imports first

- [ ] task-03: salvage local file ops from sync.py into files.py (blocks: task-01)
  - Copy `attach_file`, `detach_file`, and local-path-only `get_file` from (deleted) `sync.py` into `services/files.py`
  - Strip all S3, blob cache, HLC, change log, and signature logic from the salvaged functions
  - Add `AttachResult` and `DetachResult` result types to `models.py`

- [ ] task-04: rewrite models.py (blocks: task-03)
  - Remove: `ApiSource`, `SearchResult`, `FetchResult`, `LinkResult`, `UnlinkResult`
  - Remove: `SourceConfig`, `ApiSettings`, `LlmSettings`, `SyncConfig`, `PeerSettings`
  - Remove all peer models: `DeviceIdentity`, `PeerRecord`, `PeerIdentity`, `Peer*Result`, `VerifyEntryResult`
  - Remove all sync models: `ChangeLogEntry`, `ConflictRecord`, `PushResult`, `PullResult`, `PrefetchResult`, `UploadBlobsResult`
  - From `Reference`: remove `blob_ref` and `field_timestamps` fields
  - From `LibraryCtx`: remove `api_sources`, `llm_extract`, `peers_dir`, `data_dir`, `peer_id`, `device_id`, `sync_config`
  - From `LocalSettings`: remove `peers_dir` computed field
  - From `Settings`: keep only `local` and `citekey` blocks
  - Update `ExtractResult`: drop `method_used: Literal["pdfplumber", "llm"]`, add `agent_extraction_needed: bool = False` and `file_path: str | None = None`
  - Add `AttachResult(citekey, file_record, error)` and `DetachResult(detached, error)`

- [ ] task-05: rewrite ports.py and config.py (blocks: task-04)
  - `ports.py`: remove `SearchFn`, `FetchFn`, `LlmExtractFn`
  - `config.py`: remove `apis`, `llm`, `sync`, `peer` config block loading; keep CWD-relative resolution from spec-026

- [ ] task-06: rewrite __init__.py (blocks: task-03, task-04, task-05)
  - Remove all sync/peer/search/fetch imports, wiring, and public functions (~200 lines)
  - Wire `attach_file`, `detach_file`, `get_file` from `services/files.py`
  - Remove `make_llm_extractor` wiring and `LLM_API_KEY` env var handling
  - Remove `make_sync_storage` wiring
  - Keep all core public functions: store CRUD, staging, merge, filter, extract, files, citekeys, uid, audit, export

- [ ] task-07: update pyproject.toml and sync lock (blocks: task-05)
  - Remove `httpx[socks]`, `anthropic`, `cryptography` from `dependencies`
  - Remove `sync` optional dependency group (`minio`)
  - Run `uv sync` to regenerate `uv.lock`
  - Verify `uv run python -c "import loretools"` works with no network or credential env vars

- [ ] task-08: update extract service for agent-nudge behavior (blocks: task-04, task-06)
  - In `services/extract.py`: when pdfplumber extraction yields confidence below threshold or raises, return `ExtractResult(agent_extraction_needed=True, file_path=file_path)` instead of calling LLM
  - Update corresponding CLI handler in `cli/extract.py` to print a clear message when `agent_extraction_needed` is True

- [ ] task-09: fix broken imports, run tests green (blocks: all previous)
  - Run `uv run ruff check .` and fix any import errors
  - Run `uv run pytest tests/unit/` — all tests must pass
  - Run `grep -r "import httpx\|import anthropic\|import minio\|from cryptography" loretools/` — must return zero results

## ADR required?

No. Portability invariant is already defined in ADR-005. This spec enforces it.

## risks

1. **`services/sync.py` entanglement:** `attach_file` and `detach_file` share helpers (`_copy_to_files_dir`, `_detect_mime`) with sync-only functions. The helpers are local-only and should move with the salvaged functions — verify no sync imports leak in.

2. **`__init__.py` wiring complexity:** The current `__init__.py` is 431 lines. After stripping sync/search/peer, roughly 200 lines remain. Any missed import will cause an `ImportError` at module load time — catch this in task-09.

3. **`test_file_management.py` and `test_file_progressive_enhancement.py`:** These integration tests may exercise sync-path file operations (`sync_file`, `unsync_file`). Audit before deleting — strip any sync-dependent test cases rather than deleting the whole file.

4. **`Reference.field_timestamps` in stored data:** Existing library.json files may contain `_field_timestamps` fields on records. Since `Reference` uses `extra="allow"`, stored data will still load cleanly — no migration needed.

5. **`blob_ref` in stored data:** Same as above — `extra="allow"` means existing `blob_ref` fields in library.json will be ignored by the model but preserved in the JSON. No data loss.
