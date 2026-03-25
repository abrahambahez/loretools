# rfc: portable collection architecture

**status:** draft
**date:** 2026-03-24
**author:** abrahambahez
**context:** Claude Co-Work sandbox constraints, multi-library use case

---

## summary

Replace the global config and global install model with a **collection-scoped** architecture. A collection is a directory that contains all its reference data, config, and the binary. `scht` always operates relative to CWD — no global state, no PATH registration, no complex resolution chain. One session, one collection.

This unblocks the primary user (non-technical researcher on Claude Co-Work) and enables a natural multi-collection workflow for all users.

---

## terminology

**collection** — a self-contained working directory on which `scht` operates. All reference data, config, and the binary live inside it. `MyRefs/` is a collection.

---

## motivation

### Claude Co-Work sandbox reality

Claude Co-Work separates two storage tiers:

| tier | path | persistence |
|---|---|---|
| sandbox | `sessions/{id}/`, `/tmp/` | ephemeral — wiped on session close |
| working directory | `sessions/{id}/Library/` (mounted) | permanent across sessions |

The current architecture assumes a persistent home directory. In Co-Work, `~/.config/` and `~/.local/share/` are in the sandbox tier and are wiped each session. The only persistent storage is the user-mounted working directory.

### agents don't switch collections mid-session

`scht` is designed for AI agents as primary consumers. An agent working in a given session has a clear, scoped task within one collection. Context-switching between collections mid-session is an anti-pattern from a context engineering perspective. One session = one collection. This justifies a CWD-first, no-global-state model.

### the multi-collection case

A researcher may maintain independent collections — a personal library, shared project libraries. Each is a fully self-contained directory with its own config, citekey namespace, and sync target. No coordination overhead, no active-collection switching logic needed.

---

## proposed architecture

### collection layout

```
MyRefs/
  scht              ← single-file binary (onefile PyInstaller)
  library.json
  staging.json
  staging/
  files/
  .scholartools/
    config.json     ← collection config (auto-created on first run)
    peers/          ← peer registry and sync keys
```

Reference data lives at the collection root. Tool config lives in `.scholartools/` — hidden, out of the way, clearly not a reference file. The collection directory is the library directory.

### config resolution

One rule: **CWD is the collection root.**

`scht` looks for `.scholartools/config.json` in CWD. If absent and CWD is writable, the directory and file are auto-created with defaults. No ENV var, no `--root` flag, no global fallback.

```bash
cd ~/MyRefs && ./scht refs list          # works — CWD has config.json
./scht refs list                          # fails if CWD has no config.json
```

`library_dir` remains in `config.json` as an optional override for testing and edge cases. Its default is CWD. It is not shown in the auto-generated config.

### binary distribution: onefile

The Linux binary is built with PyInstaller `--onefile`. A single self-contained executable (~100 MB) instead of a directory bundle. Slower cold start (~2 s) but simpler to copy, distribute, and manage.

The binary lives in the collection directory. It is persistent across Co-Work sessions because it is inside the mounted working directory. No setup script is needed for subsequent sessions.

### Co-Work session lifecycle

**first session (one-time setup, agent-guided):**

1. User downloads the release zip in their browser (contains `scht` binary + `scholartools-manager` skill zip)
2. User opens Claude Co-Work, mounts their research folder, uploads both files
3. User prompts: *"Help me set up scholartools for a reference collection"*
4. Agent (guided by `scholartools-manager` skill) executes setup:
   ```bash
   # copy binary to collection directory and make executable
   cp /path/to/uploaded/scht /path/to/MyRefs/scht
   chmod +x /path/to/MyRefs/scht

   # verify
   cd /path/to/MyRefs && ./scht refs list
   # config.json auto-created with defaults
   ```
5. Agent asks user preferences (email for API polite pool, citekey pattern, etc.) and writes `config.json`

**subsequent sessions:**

```bash
cd /path/to/MyRefs && ./scht refs list
```

The binary is already in the collection directory. No copying, no setup. The agent cd's to the collection and runs commands.

### installation delivery

The release zip for the primary user contains:
- `scht` — single-file Linux x86_64 binary
- `scholartools-manager-en-vX.Y.Z.zip` — bundled skill

The user uploads both to Claude Desktop. The skill guides the agent through setup. The user never touches a terminal.

---

## new skill: scholartools-manager

Replaces the current `scholartools-config` skill. Scope: first-time setup, session start verification, and config reference. The agent reads this skill and knows how to:

1. Install the binary into the collection directory
2. Create or validate `config.json` based on user preferences
3. Verify the collection is operational before starting any research task
4. Document all config options and their defaults

This skill is the primary onboarding surface for non-technical users.

---

## codebase impact

### changed

| file | change |
|---|---|
| `scholartools/config.py` | Remove `CONFIG_PATH` constant. Resolve to `Path.cwd() / ".scholartools" / "config.json"`. Auto-create dir + file with defaults if absent. |
| `scholartools/models.py` | `LocalSettings.library_dir` default changes to `Path.cwd()` (resolved at load time, not model definition time). |
| `.build/pyinstaller.spec` | Switch to `--onefile` mode. Remove `COLLECT` step. Single EXE output. |
| `.github/workflows/build-release.yml` | Adjust zip step — zip single binary file, not a directory. |
| `skills/en/scholartools-config/` | Replaced by `skills/en/scholartools-manager/`. |
| `skills/es/scholartools-config/` | Replaced by `skills/es/scholartools-manager/`. |

### removed

| thing | reason |
|---|---|
| `CONFIG_PATH = Path.home() / ...` | Replaced by CWD resolution |
| `LocalSettings` global default path | CWD is the new default |
| `.build/install.sh` | No longer the install model. Replaced by agent-guided setup via skill. |
| `.build/install.ps1` | Irrelevant — primary user is on Co-Work (Linux sandbox). |
| `setup.sh` in zip | Onefile binary + agent skill makes it unnecessary. |

### unchanged

- All service functions
- All adapter functions
- All Pydantic models except `LocalSettings.library_dir` default
- All public Python API
- Distributed sync (RFC-001) — sync config lives in `config.json` as before
- Skills delivery mechanism — zip download, load as project instruction in Claude Desktop

---

## risks

**R1 — test isolation**: Unit tests calling `load_settings()` will resolve to the repo root as CWD. A `.scht/` or `config.json` could be auto-created there. Mitigation: `conftest.py` sets CWD to a tmp directory or patches `Path.cwd()` before any test that calls `load_settings()`.

**R2 — existing beta users**: Any user with `~/.config/scholartools/config.json` will see it ignored. Mitigation: zero real users; document in CHANGELOG. No migration path needed.

**R3 — onefile startup time**: First run extracts to a temp dir (~2 s). Acceptable for agent use where startup cost is negligible relative to API call latency.

**R4 — binary size in collection**: A 100 MB binary in every collection directory. For users with multiple collections this multiplies. Acceptable for now; a future `~/.scholartools/collections.json` index (noted as not-now) could introduce a shared binary location.

---

## resolved decisions

1. **Release zip contents**: two separate downloads from the releases page, as currently — one zip for the binary, one zip per skill.
