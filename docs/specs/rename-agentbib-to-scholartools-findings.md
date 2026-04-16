# findings: rename loretools → loretools

task: map the full blast radius of renaming `loretools` → `loretools`
date: 2026-03-09
status: complete — no implementation, read-only analysis

---

## files affected

### 1. Python package directory — src/loretools/ → src/loretools/

The entire directory must be renamed. Every file inside it contains intra-package imports that use `loretools.*` and must be updated.

| file | reason |
|------|--------|
| `src/loretools/__init__.py` | 9 import lines: `from loretools.adapters…`, `from loretools.apis…`, `from loretools.config…`, `from loretools.models…`, `from loretools.services…`; also docstring on line 85 references `.loretools/config.json` |
| `src/loretools/config.py` | lines 50, 52, 55, 74, 76: env var names `SCHOLARTOOLS_CONFIG`, `SCHOLARTOOLS_LIBRARY_PATH`, `SCHOLARTOOLS_FILES_DIR`; config file paths `.loretools/config.json` and `~/.config/loretools/config.json` |
| `src/loretools/models.py` | line 5: `from loretools.ports import …` |
| `src/loretools/ports.py` | no internal imports of package name, but lives inside the directory |
| `src/loretools/adapters/local.py` | line 5: `from loretools.ports import …` |
| `src/loretools/services/extract.py` | line 9: `from loretools.models import …` |
| `src/loretools/services/fetch.py` | line 6: `from loretools.models import …` |
| `src/loretools/services/search.py` | line 6: `from loretools.models import …` |
| `src/loretools/services/files.py` | line 12: `from loretools.models import …`; also line 3 prose comment mentions "loretools original" |
| `src/loretools/services/store.py` | line 3: `from loretools.models import …`; line 13: `from loretools.services import citekeys` |
| `src/loretools/services/citekeys.py` | lives inside directory; verify no internal imports (not read, but affected by directory rename) |
| `src/loretools/apis/anthropic_extract.py` | line 8: `from loretools.ports import …` |
| `src/loretools/apis/crossref.py` | line 3: `from loretools.ports import …`; line 9: User-Agent header string `"loretools/0.1 (mailto:{email})"` — this is also an externally visible identifier sent to Crossref API |
| `src/loretools/apis/arxiv.py` | line 6: `from loretools.ports import …` |
| `src/loretools/apis/semantic_scholar.py` | line 3: `from loretools.ports import …` |
| `src/loretools/apis/google_books.py` | line 5: `from loretools.ports import …` |
| `src/loretools/apis/latindex.py` | line 3: `from loretools.ports import …` |
| `src/loretools/mcp.py` | referenced in manifest.json as entry point; must move to `src/loretools/mcp.py` |

### 2. Python imports — tests/

| file | lines | reason |
|------|-------|--------|
| `tests/unit/test_search.py` | 5–6 | `from loretools.models import …`, `from loretools.services.search import …` |
| `tests/unit/test_fetch.py` | 3–4 | `from loretools.models import …`, `from loretools.services.fetch import …` |
| `tests/unit/test_config.py` | 5; 16, 37, 45, 55, 62, 69 | `from loretools.config import …`; env var name `SCHOLARTOOLS_CONFIG` in 6 monkeypatch calls |
| `tests/unit/test_store.py` | 1–2 | `from loretools.models import …`, `from loretools.services.store import …` |
| `tests/unit/test_citekeys.py` | 1 | `from loretools.services.citekeys import …` |
| `tests/unit/test_files.py` | 3–4 | `from loretools.models import …`, `from loretools.services.files import …` |
| `tests/unit/test_extract.py` | 5–6; 69, 95, 111, 123, 134 | `from loretools.models import …`, `from loretools.services.extract import …`; 5 `pytest.mock.patch` strings using `"loretools.services.extract._extract_with_pdfplumber"` — these are dotted module path strings, not imports, and must match the installed package name exactly |
| `tests/unit/test_local_adapter.py` | 1 | `from loretools.adapters.local import …` |
| `tests/unit/test_models.py` | 4 | `from loretools.models import …` |

### 3. pyproject.toml and build config

| file | lines | reason |
|------|-------|--------|
| `pyproject.toml` | 6: `name = "loretools"` | PyPI package name |
| `pyproject.toml` | 25: `packages = ["src/loretools"]` | hatchling source package declaration |
| `uv.lock` | 6: `name = "loretools"` | lockfile entry; regenerated automatically by `uv sync` after pyproject.toml change, but must be committed |

### 4. Config file paths — .loretools/ discovery chain

| file | lines | reason |
|------|-------|--------|
| `src/loretools/config.py` | 50: `SCHOLARTOOLS_CONFIG` env var | env var name; callers who set this must update their environment |
| `src/loretools/config.py` | 52: `.loretools/config.json` | project-local config discovery path |
| `src/loretools/config.py` | 55: `~/.config/loretools/config.json` | global config discovery path |
| `src/loretools/config.py` | 74: `SCHOLARTOOLS_LIBRARY_PATH` | env var name |
| `src/loretools/config.py` | 76: `SCHOLARTOOLS_FILES_DIR` | env var name |
| `/home/sabhz/archivo/idearium/.loretools/config.json` | — | live runtime config file at vault root; if the discovery path changes to `.loretools/config.json`, this file must be moved or the old path kept as a compatibility alias |
| `manifest.json` | 17–18, 31–43 | `SCHOLARTOOLS_LIBRARY_PATH`, `SCHOLARTOOLS_FILES_DIR` as user_config keys; these are the env vars injected into the MCP server process |

### 5. Docs — all .md files

| file | lines | reason |
|------|-------|--------|
| `CLAUDE.md` | 1, 6, 49, 50, 57, 82 | project heading, path references throughout |
| `README.md` | 1, 8–9, 15, 35–57, 68, 74 | package name in heading, git clone URL, import examples (`import loretools`), config path `.loretools/config.json`, MCP artifact name `loretools.mcpb` |
| `docs/tech.md` | 1, 25, 31, 36, 66 | document heading; architecture diagram ASCII paths; prose |
| `docs/structure.md` | 1 | document heading |
| `docs/vision.md` | 1, 23 | heading and prose |
| `docs/product.md` | 1, 5, 33–34 | heading; prose; path `~/.loretools/library.json`, `~/.loretools/files/` |
| `docs/feats/001-core-library.md` | 8, 45, 62, 86, 243 | prose; field comment; config path in design doc |
| `docs/feats/002-staging-workflow.md` | 32, 38, 40, 43, 51, 70 | all `~/.loretools/` path references in design doc |
| `docs/adr/001-hexagonal-result-types.md` | 7 | prose mention |
| `docs/adr/002-pdf-extraction.md` | 7 | prose mention |
| `docs/adr/003-httpx.md` | 7, 10 | prose mentions; `src/loretools/apis/` path in doc |
| `docs/adr/004-pydantic-all-the-way.md` | 7, 12 | prose mention; `src/loretools/models.py` path in doc |
| `specs/001-core-library.md` | 29 | `src/loretools/` path in task description |
| `claude-progress.txt` | session 1 entry | multiple references to `src/loretools/`, `loretools.services`, etc. in completed task descriptions |

### 6. Tests — additional notes

Covered above under group 2. The `pytest.mock.patch` strings in `tests/unit/test_extract.py` at lines 69, 95, 111, 123, 134 (`"loretools.services.extract._extract_with_pdfplumber"`) are runtime module path strings that Python resolves against the installed package. They will silently pass or fail to patch if not updated alongside the package rename.

### 7. Skills / shell scripts

**Inside the project (`scripts/loretools/`):**

| file | lines | reason |
|------|-------|--------|
| `init.sh` | 8, 17 | echo string "loretools health check"; `import loretools` in inline python |

**Outside the project — vault-level (`/home/sabhz/archivo/idearium/`):**

| file | lines | reason |
|------|-------|--------|
| `scripts/research_session.py` | 1–3, 23, 55, 63, 90, 98, 121, 133, 138, 158, 178, 197, 217, 235 | docstring; `import loretools`; 11 calls to `loretools.*` functions |
| `scripts/rename_citekey.py` | 17, 34, 38 | `import loretools`; 2 calls to `loretools.*` functions |
| `scripts/backup_bib.sh` | 3, 11, 12, 43 | prose comment; `LIB_GIST_ID_FILE="$VAULT/.loretools/gist_id"`; `LOG_FILE="$VAULT/.loretools/backup_log.txt"`; gist description string "lib.json — idearium loretools" |
| `claude/skills/loretools/SKILL.md` | 2 | `name: loretools-research` |
| `claude/skills/loretools/research_session.py` | 2–3, 36, 41, 50, 73, 78, 86, 102, 110, 122, 127, 147–148, 168–169, 183, 189 | docstring; `import loretools`; 10 calls to `loretools.*` functions; this is a near-duplicate of `scripts/research_session.py` |
| `claude/skills/gestionar-citekeys/SKILL.md` | 35 | inline python one-liner: `import loretools; print(loretools.delete_reference(…))` |
| `CLAUDE.md` (vault root) | 77 | `.loretools/gist_id` and `.loretools/backup_log.txt` paths in backup instructions |

**Vault filesystem:**

| path | reason |
|------|--------|
| `/home/sabhz/archivo/idearium/.loretools/config.json` | live runtime config directory used by `scripts/research_session.py`; if discovery path changes, this must move |
| `/home/sabhz/archivo/idearium/.loretools/gist_id` | not confirmed to exist, but backup_bib.sh writes it here |
| `/home/sabhz/archivo/idearium/.loretools/backup_log.txt` | not confirmed to exist, but backup_bib.sh writes it here |
| `claude/skills/loretools/` | skill directory named after the package; may need to be renamed to `claude/skills/loretools/` |

### 8. Other files

| file | lines | reason |
|------|-------|--------|
| `manifest.json` | 3, 11, 14, 17–18, 31, 37 | `"name": "loretools"`; entry_point path `src/loretools/mcp.py`; args path; three `SCHOLARTOOLS_*` env var keys |
| `feature_list.json` | — | no occurrences of `loretools` — no change needed |
| `.venv/bin/activate` | 81, 101–102 | `VIRTUAL_ENV` path (absolute, self-corrects); `VIRTUAL_ENV_PROMPT="loretools"` — cosmetic, auto-regenerated by `uv sync` |
| `.venv/bin/activate_this.py` | 49 | `"loretools" or os.path.basename(base)` — cosmetic, auto-regenerated |
| `.venv/lib/python3.13/site-packages/_loretools.pth` | — | filename contains package name; content is the `src/` path; auto-regenerated by `uv sync` after install |
| `.venv/lib/python3.13/site-packages/loretools-0.2.0.dist-info/` | entire directory | dist-info directory named after package; all files inside (METADATA, RECORD, direct_url.json, uv_build.json, uv_cache.json) auto-regenerated by `uv sync` |
| `evals/rubric.md` | — | no occurrences of `loretools` — no change needed |

---

## cross-dependencies

**Public import surface (callers outside the project):**
- `scripts/research_session.py`, `scripts/rename_citekey.py`, and both skill files do `import loretools` at the top level. These resolve against the installed editable package. The rename breaks all of them simultaneously on the same `uv sync` that renames the package.
- `claude/skills/gestionar-citekeys/SKILL.md` contains a one-liner that does `import loretools` — not a Python file but executed by copy-paste or shell eval.

**Env vars as implicit interface:**
- `SCHOLARTOOLS_CONFIG`, `SCHOLARTOOLS_LIBRARY_PATH`, `SCHOLARTOOLS_FILES_DIR` are read in `config.py` and declared in `manifest.json`. Any researcher's shell profile, `.env`, or MCP config that sets these will break silently — the library will fall back to defaults without warning.

**pytest.mock.patch strings:**
- The 5 patch strings in `tests/unit/test_extract.py` (`"loretools.services.extract._extract_with_pdfplumber"`) are dotted import paths as strings. They are not caught by an IDE rename and will fail silently (patch applies to wrong module) rather than raising ImportError.

**MCP artifact name:**
- `README.md` line 74 references `loretools.mcpb` as the distributed artifact name. If this is also the published binary name, downstream users' instructions would break.

**User-Agent header:**
- `src/loretools/apis/crossref.py` line 9: `f"loretools/0.1 (mailto:{email})"` — sent to Crossref's API on every request. Crossref uses this for rate-limit tracking and contact. Changing it is safe but means a new identity in their logs.

---

## data/schema implications

**Runtime config file path:**
- The discovery chain in `config.py` looks for `.loretools/config.json` (project-local) and `~/.config/loretools/config.json` (global). The live vault config lives at `/home/sabhz/archivo/idearium/.loretools/config.json`. If the rename changes these discovery paths to `.loretools/config.json` and `~/.config/loretools/config.json`, the existing config file becomes invisible and the library silently falls back to defaults (no error, no warning). This is a silent runtime regression.

**No schema changes to data files:**
- `lib.json`, `library.json`, and any stored reference JSON use CSL-JSON + the `_file` / `_warnings` fields from the `Reference` model. None of these fields embed the package name. Data files survive the rename untouched.

**dist-info directory name:**
- `loretools-0.2.0.dist-info/` is named by convention `{name}-{version}.dist-info`. After rename and `uv sync`, uv will install `loretools-0.2.0.dist-info/`. The old dist-info directory will be left behind unless `uv sync` cleans it up — worth verifying.

---

## risks

1. **Silent config loss** (HIGH): The config discovery path `.loretools/config.json` is hardcoded. If it changes to `.loretools/config.json`, the live vault config at `/home/sabhz/archivo/idearium/.loretools/config.json` becomes invisible. The library falls back to defaults with no error. This silently changes `library_path` and `files_dir` for every live operation.

2. **Silent mock patch failure in tests** (MEDIUM): The 5 `pytest.mock.patch("loretools.services.extract._extract_with_pdfplumber", …)` strings in `test_extract.py` will not raise an ImportError if not updated — they will patch the wrong or nonexistent module, causing tests to pass while not actually mocking the target. The test suite would show green with broken test coverage.

3. **Vault-level scripts break simultaneously** (MEDIUM): `scripts/research_session.py` and `scripts/rename_citekey.py` both do `import loretools` at module level. They will fail with `ModuleNotFoundError` immediately after `uv sync` completes the rename, before any other changes are made to those files. Since these scripts are used by the researcher daily, there is zero tolerance window.

4. **Env vars set in researcher's environment** (MEDIUM): `SCHOLARTOOLS_CONFIG`, `SCHOLARTOOLS_LIBRARY_PATH`, `SCHOLARTOOLS_FILES_DIR` may be set in the researcher's `.zshrc`, `.env`, or Claude Desktop MCP config. These are external to the repository and cannot be found by grep. After rename, if env var names change to `SCHOLARTOOLS_*`, those variables will stop being read silently.

5. **Old dist-info leftover** (LOW): `.venv/lib/python3.13/site-packages/loretools-0.2.0.dist-info/` may persist after the rename if uv does not automatically clean it up. Two dist-infos for different names pointing to the same editable install could confuse tooling.

6. **MCP artifact name in README** (LOW): `loretools.mcpb` is mentioned as the distribution artifact. If this file is actually published or shared, downstream users would need to be notified.

7. **Crossref User-Agent string** (LOW): The string `"loretools/0.1 (mailto:{email})"` is sent externally. Not a breaking change, but worth updating for consistency and honest identification.

8. **`claude/skills/loretools/` directory name** (LOW): The skill directory is named `loretools`. Renaming it is optional (it's not a Python import path), but leaving it creates a confusing inconsistency.

---

## open questions

1. **Config path strategy** — should the discovery chain change from `.loretools/` to `.loretools/`, or should both paths be checked for backward compatibility? The live vault config at `/home/sabhz/archivo/idearium/.loretools/config.json` is the immediate concern. **Decision required before implementation.** If both paths are supported, this adds a permanent compatibility shim that conflicts with the lean code principle.

2. **Env var names** — should `SCHOLARTOOLS_CONFIG`, `SCHOLARTOOLS_LIBRARY_PATH`, `SCHOLARTOOLS_FILES_DIR` be renamed to `SCHOLARTOOLS_*`? The researcher may have these set in their environment outside the repo. Renaming them is a breaking change to any external configuration. **Explicit decision required — affects `config.py`, `manifest.json`, `tests/unit/test_config.py`, and any environment not under version control.**

3. **Vault `.loretools/` directory migration** — if config paths change, the directory `/home/sabhz/archivo/idearium/.loretools/` must be renamed to `.loretools/`. This directory also contains `gist_id` and `backup_log.txt` used by `scripts/backup_bib.sh`. **Decision required: rename directory, update backup_bib.sh, or decouple backup dir from config dir.**

4. **`scripts/research_session.py` vs `claude/skills/loretools/research_session.py`** — these appear to be near-duplicates. Should both be updated, and should the skill directory be renamed? **Not a blocker but must be decided to avoid inconsistency.**

5. **ADR required?** — the env var naming convention and config file path schema are architectural decisions that affect external integrators (researchers setting env vars, MCP users). If `SCHOLARTOOLS_*` → `SCHOLARTOOLS_*` and `.loretools/` → `.loretools/`, this is a breaking public API change in the configuration surface. **An ADR is recommended** to record the decision, rationale, and migration path. Suggested: `docs/adr/005-rename-to-loretools.md`.

6. **Version bump** — the rename constitutes a breaking change in the package name (a new PyPI name). Should the version go from `0.2.0` to `0.3.0` or `1.0.0`? **Decision required before updating `pyproject.toml`.**

7. **GitHub repository name** — `README.md` contains `git clone https://github.com/abrahambahez/loretools`. If the GitHub repo is also renamed, the clone URL changes. If not, the discrepancy between repo name and package name must be documented.
