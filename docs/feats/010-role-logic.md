# 010: role logic — per-peer identity in config and admin/contributor roles

**version:** v0.2

## context

Feats 007 (peer-management) and 008 (distributed-sync-phase1) built the signing
infrastructure and the change log protocol. Both work correctly in isolation, but they
were wired with a shortcut: `_build_ctx()` hardcodes `admin_peer_id="_admin"` and
`admin_device_id="_admin"` as the signing identity for every peer on every machine.

This breaks multi-peer sync in a specific way:

- Every peer pushes to `changes/_admin/{hlc}.json`
- `pull()` skips all entries where `peer_id == ctx.admin_peer_id` — which is `"_admin"`
  for everyone — so **every peer skips every entry in the bucket**, including those from
  other researchers
- Two researchers pushing to the same bucket stomp on each other's filenames under
  `changes/_admin/`

The RFC already described the correct layout as `changes/{peer_id}/{hlc}.json` per peer.
The implementation never reached that because the public API wasn't wired to read the
peer's identity from config.

This feat closes that gap by introducing `peer_id` and `device_id` as first-class config
fields, and formalizing two roles — **admin** and **contributor** — that govern who can
register peers and who can only push/pull.

## what changes

### `config.json` — new `peer` block

```json
{
  "peer": {
    "peer_id": "sabhz",
    "device_id": "laptop"
  }
}
```

`peer_id` and `device_id` are required when a `sync` block is present. They identify
this machine's signing identity. The role (admin vs contributor) is resolved at runtime
from the peer directory entry — it is not stored in `config.json`.

`load_settings()` raises a `ValueError` with a clear message if `sync` is present and
`peer` is absent. Local-only setups (no `sync` block) are unaffected — `peer` remains
optional.

### `Settings` — `PeerSettings` model

```python
class PeerSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    peer_id: str
    device_id: str
```

Added as `Settings.peer: PeerSettings | None = None`.

### `LibraryCtx` — rename `admin_peer_id` / `admin_device_id` → `peer_id` / `device_id`

`LibraryCtx.admin_peer_id` and `admin_device_id` are renamed to `peer_id` and
`device_id`. The fields were never exclusively about admin peers — they were always "the
peer signing on this machine." Renaming removes the misleading implication.

**Breaking change scope:** internal only. `LibraryCtx` is not part of the public API.
A pre-implementation code search must confirm no service imports `admin_peer_id` or
`admin_device_id` directly; all usages go through `ctx.admin_peer_id` which is renamed
in one place.

### `_build_ctx()` — read from config, not hardcoded

```python
# before
admin_peer_id="_admin",
admin_device_id="_admin",

# after
peer_id=s.peer.peer_id,
device_id=s.peer.device_id,
```

### key path resolution

`_load_admin_key()` in `services/peers.py` and `_load_privkey()` in `services/sync.py`
both look up:

```
~/.config/scholartools/keys/{ctx.peer_id}/{ctx.device_id}.key
```

Structure unchanged — only the values change from hardcoded `_admin/_admin` to whatever
is in config. If the key file does not exist, both functions return `None` and the
caller surfaces a `Result(ok=False, error="local device keypair not found")`.

### push/pull routing

- `push()` writes to `changes/{peer_id}/{hlc}.json` — now correct per peer
- `pull()` skips `changes/{peer_id}/` — now correctly skips only own entries
- `sync_composite.py` writes change log entries with `peer_id` from ctx — now correct

### roles

Roles live in the peer directory (`{peers_dir}/{peer_id}` → `DeviceIdentity.role`).
Two roles:

| role | can push own changes | can pull and verify | can register / revoke peers |
|---|---|---|---|
| `admin` | yes | yes | yes |
| `contributor` | yes | yes | no |

`DeviceIdentity.role` currently defaults to `"peer"`. This feat renames the default to
`"contributor"`. Existing records with `role="peer"` are treated as equivalent to
`"contributor"` at runtime — no migration or backfill needed; the role value is advisory
and never gated on an exact string match beyond `"admin"`.

**Role check timing.** `peer_register()`, `peer_add_device()`, and `peer_revoke()` check
the caller's role as the **first step after loading the caller's keypair** from the peer
directory. Sequence:

1. Load `ctx.peer_id` / `ctx.device_id` keypair from `~/.config/scholartools/keys/`
2. If key not found → `Result(ok=False, error="local device keypair not found")`
3. Load caller's peer directory entry
4. If entry not found → `Result(ok=False, error="caller peer not registered")`
5. If `entry.role != "admin"` → `Result(ok=False, error="caller is not an admin")`
6. Proceed with the operation

All failures return a typed Result — no exceptions raised.

### `peer_register_self()`

New public function. Self-signs a peer record with `role="admin"` for the first peer on
a fresh deployment, without requiring a pre-existing admin key.

**Valid only when the peer directory contains no files.** Specifically:

- If `{peers_dir}/` does not exist → proceed (treat as empty)
- If `{peers_dir}/` exists and contains zero files → proceed
- If `{peers_dir}/` exists and contains any file → `Result(ok=False, error="peer directory is not empty; use peer_register() with an existing admin")`

This prevents accidental self-promotion on an existing deployment. The check is on file
count, not on whether the caller's own entry exists — any pre-existing entry means
bootstrap is over.

### bootstrap change

The `_admin/_admin` keypair concept is retired. Bootstrap for a fresh deployment:

1. `peer_init(peer_id, device_id)` — creates the keypair
2. `peer_register_self()` — self-signs, writes `{peers_dir}/{peer_id}` with `role="admin"`

For subsequent peers (contributors or additional devices), the admin calls
`peer_register()` or `peer_add_device()` as before.

### `bootstrap_identity.py` update

The script gains a `--role` flag (default: `contributor`). After `peer_init` it prints
the `peer` block for the user to add to `config.json` — it does **not** write to
`config.json` directly.

For `--role admin` it also calls `peer_register_self()` automatically. For
`--role contributor` it only calls `peer_init` and prints the public key for the admin
to register via `peer_register()`.

```bash
# first peer on a new deployment (admin)
uv run python scripts/bootstrap_identity.py \
  --peer-id sabhz --device-id laptop --role admin

# output:
# keypair created at ~/.config/scholartools/keys/sabhz/laptop.key
# admin self-registered in peers/sabhz
# add to config.json:
#   "peer": { "peer_id": "sabhz", "device_id": "laptop" }

# adding a second researcher (contributor)
uv run python scripts/bootstrap_identity.py \
  --peer-id elena --device-id desktop --role contributor

# output:
# keypair created at ~/.config/scholartools/keys/elena/desktop.key
# add to config.json:
#   "peer": { "peer_id": "elena", "device_id": "desktop" }
# share this public key with the admin to register:
#   <base64 public key>
```

### `remote-setup.md` update

Step 3 collapses to one command. A new section covers adding a second researcher. The
updated steps are drafted as part of the spec, not this design doc.

## what this does not change

- The `peers/` directory layout and Ed25519 signing protocol — unchanged
- `pull()` verification logic — unchanged; still rejects unregistered peers
- The blob sync layer (`link_file`, `get_file`, `prefetch_blobs`) — unchanged
- The public API surface (`push`, `pull`, `create_snapshot`, etc.) — unchanged
- Existing local-only setups (no `sync` block) — unchanged

## what this does not solve

- **S3 credential bypass.** A peer with direct bucket credentials can write arbitrary
  objects to `changes/`. Signed entries still verify correctly on pull, so unsigned or
  malformed objects are rejected — but a compromised credential can inject garbage.
  Mitigation is at the IAM layer (scoped per-peer credentials), not in this protocol.
- **Per-field or per-record read ACLs** — S3 bucket policies are the appropriate layer
- **Role elevation without re-registration** — revoke and re-register with the new role
- **Automatic role verification on push** — the peer directory is append-only via the
  public API; enforcement is implicit

## design decisions

**Role in peer directory, not in config.** The peer directory is the trust anchor —
it is signed by the admin and shared across peers via the bucket. Storing role in
`config.json` would let any peer self-promote. The directory entry is the authoritative
source.

**`peer_register_self()` instead of `_admin` bootstrap.** The old approach created a
ghost identity (`_admin`) with no correspondence to any real researcher. Self-registration
on an empty directory is the honest primitive: the first peer declares themselves admin
with no prior authority — which is exactly the correct trust model for a new deployment.

**Print, don't write `config.json`.** The bootstrap script prints the `peer` block
rather than mutating `config.json` silently. Config is the user's file; the script is an
assistant, not an owner.

**`"peer"` → `"contributor"`.** "Peer" was ambiguous — everything in the system is a
peer. "Contributor" matches the mental model. Old `"peer"` values are treated as
`"contributor"` at runtime with no migration.

**Role check as first step, typed Result always.** Failing fast before any mutation
keeps error paths clean. Returning `Result(ok=False)` rather than raising keeps the
public boundary consistent with the rest of the codebase.
