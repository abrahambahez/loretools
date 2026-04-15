# spec: 026-portable-root-architecture — collection-scoped config, onefile binary

## findings

From docs/rfc/002-portable-root-architecture.md:

**Problem:** The current global config model (`~/.config/scholartools/config.json`) breaks in Claude Co-Work's sandbox architecture where `~/.config/` is ephemeral. The primary user (non-technical researcher on Co-Work) cannot maintain persistent reference libraries across sessions.

**Solution:** Replace global config + global install with a **collection-scoped architecture**:
- A collection is a self-contained directory containing reference data, config, and the binary
- `scht` always operates relative to CWD — no global state, no PATH registration
- Config resolves to `.scholartools/config.json` in CWD, auto-created if missing
- `LocalSettings.library_dir` defaults to CWD
- Binary is PyInstaller onefile (~100 MB) — lives in the collection directory, persists across Co-Work sessions
- New skill `scholartools-manager` replaces `scholartools-config` for first-time setup

**Current state:**
- `config.py`: `CONFIG_PATH = Path.home() / ".config" / "scholartools" / "config.json"`
- `models.py`: `LocalSettings.library_dir` default is `Path.home() / ".local/share/scholartools"`
- `.build/pyinstaller.spec`: directory bundle with `COLLECT` step
- `skills/*/scholartools-config/`: current config skill

## objective

Convert the global config model to CWD-relative `.scholartools/config.json`, change `LocalSettings.library_dir` default to `Path.cwd()`, convert the PyInstaller build to onefile mode, replace the `scholartools-config` skill with `scholartools-manager`, and remove the old install scripts. This unblocks the primary user on Claude Co-Work by making the collection directory the single source of persistence.

## acceptance criteria (EARS format)

- when a researcher reads `docs/getting-started.md`, they must find step-by-step Claude Co-Work setup instructions covering: download release zip, upload to Co-Work, prompt the manager skill, verify collection
- when a researcher reads `README.md` install section, they must find the Co-Work setup path as the primary install method, with the technical CLI path clearly separated
- when `README.md` config section is read, the documented config path must be `.scholartools/config.json` (CWD-relative), not `~/.config/scholartools/config.json`
- when `README.md` config section documents `local.library_dir`, the documented default must be the collection directory (CWD), not `~/.local/share/scholartools`
- when `load_settings()` is called in a directory containing `.scholartools/config.json`, the system must load config from that CWD-relative path
- when `load_settings()` is called in a writable directory without `.scholartools/config.json`, the system must auto-create the directory and file with defaults and return loaded settings
- when `load_settings()` is called and CWD has no `.scholartools/config.json` and cannot be created, the system must raise a clear error — it must never fall back to a global path
- when `LocalSettings.library_dir` is not set in config, the system must default to `Path.cwd()` resolved at load time
- when a unit test calls `load_settings()`, the system must resolve config to a test-scoped temp directory, not the repo root
- when PyInstaller builds the CLI, the system must produce a single `scht` executable file (not a directory bundle)
- when the release zip is packaged, it must contain a single `scht` binary file (not a `scht/` directory)
- when `.build/pyinstaller.spec` is inspected, the `COLLECT` step must be absent
- when the release workflow runs, it must not upload `.build/install.sh` or `.build/install.ps1`
- when an agent reads the `scholartools-manager` skill, it must know how to install the binary into a collection, create or validate `config.json`, and verify the collection is operational
- when `skills/en/scholartools-config/` or `skills/es/scholartools-config/` are searched, they must not exist

## tasks

- [ ] task-01: update `config.py` — CWD-relative config resolution (blocks: none)
  - Remove `CONFIG_PATH` constant
  - Resolve config path as `Path.cwd() / ".scholartools" / "config.json"` inside `load_settings()`
  - Auto-create `.scholartools/` and `config.json` with defaults when missing and writable
  - Raise `FileNotFoundError` with clear message if directory not writable and config missing

- [ ] task-02: update `models.py` — `LocalSettings.library_dir` defaults to CWD (blocks: task-01)
  - Change `default_factory` from `lambda: Path.home() / ".local/share/scholartools"` to `lambda: Path.cwd()`
  - No breaking change for configs that already specify `library_dir`

- [ ] task-03: isolate `load_settings()` in tests (blocks: task-01, task-02)
  - Add `conftest.py` fixture that patches `Path.cwd()` (or `monkeypatch.chdir`) to `tmp_path` for tests that call `load_settings()`
  - Ensure no `.scholartools/` directory is ever created in the repo root during test runs

- [ ] task-04: convert PyInstaller spec to onefile mode (blocks: none)
  - Update `.build/pyinstaller.spec`: set `exclude_binaries=False` on `EXE`, pass all binaries and datas into `EXE`, remove `COLLECT` block
  - Verify build output is a single `scht` file under `dist/`

- [ ] task-05: update CI to package onefile binary and remove install scripts (blocks: task-04)
  - Update zip step in `build-release.yml` to zip the single `scht` file, not `scht/` directory
  - Remove the step that uploads `.build/install.sh` and `.build/install.ps1`
  - Verify no other CI step references the old directory bundle structure

- [ ] task-06: create `scholartools-manager` skill, remove `scholartools-config` (blocks: none)
  - Create `skills/en/scholartools-manager/SKILL.md` — covers: binary install into collection, config creation from user preferences, session-start verification
  - Create `skills/es/scholartools-manager/SKILL.md` (Spanish equivalent)
  - Delete `skills/en/scholartools-config/` and `skills/es/scholartools-config/`

- [ ] task-07: write `docs/getting-started.md` — Claude Co-Work setup guide (blocks: task-06)
  - Primary audience: non-technical researcher, zero terminal experience
  - Cover the full first-session flow: download release zip from GitHub releases page → open Claude Co-Work → mount research folder → upload `scht` and `scholartools-manager` skill zip → prompt the manager skill to complete setup
  - Cover subsequent-session flow: open Co-Work → mount folder → ask agent to verify collection → start working
  - Include the collection directory layout after setup (`.scholartools/config.json`, `library.json`, `files/`, `staging/`, `staging.json`)
  - Include a config reference section explaining each key and its default in the collection model
  - Do NOT include shell commands the user must run themselves — the agent handles all shell operations

- [ ] task-08: update `README.md` — remove global install path, add collection model (blocks: task-07)
  - Replace the `curl | bash` / `irm | iex` install blocks with: primary method = Co-Work (link to `docs/getting-started.md`), secondary method = direct binary download for technical users
  - Remove uninstall instructions that reference `install.sh` / `install.ps1`
  - Update config section: path is `.scholartools/config.json` inside the collection directory; `local.library_dir` default is the collection directory (CWD); remove the `~/.config/` and `~/.local/share/` references

- [ ] task-09: remove old install scripts and update CHANGELOG (blocks: task-05, task-06, task-08)
  - Delete `.build/install.sh` and `.build/install.ps1`
  - Add CHANGELOG entry under new version: `### Removed` for install scripts and config skill; `### Changed` for config resolution, binary format, and README; `### Skills` noting `scholartools-manager` replaces `scholartools-config`

## ADR required?

No. Architecture is fully resolved in RFC-002. No open trade-offs.

## risks

1. **Test isolation:** `load_settings()` auto-creates `.scholartools/` in CWD — could pollute repo root if tests don't isolate CWD. Mitigation: task-03 conftest fixture.

2. **Existing beta users:** `~/.config/scholartools/config.json` silently ignored after upgrade. Mitigation: zero real users; document in CHANGELOG.

3. **Onefile cold start:** ~2 s on first extraction. Acceptable for agent use where API latency dominates.

4. **CI zip change:** release consumers expecting `scht/scht` path inside zip must update. Mitigation: document in CHANGELOG; no known consumers.

5. **README discoverability:** GitHub README is many users' first contact. If the Co-Work setup path is buried, technical users may attempt the old global install flow on a machine where the binary won't be on PATH. Mitigation: task-08 makes Co-Work the clear primary path, with the direct binary download as an explicit secondary option.
