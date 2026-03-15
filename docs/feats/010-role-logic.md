# 010: role logic — per-peer identity in config and admin/contributor roles

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

### `Settings` and `LocalSettings` — `PeerSettings` model

```python
class PeerSettings(BaseModel):
    peer_id: str
    device_id: str
```

Added as `Settings.peer: PeerSettings | None = None`. Validated: if `sync` is present
and `peer` is absent, `load_settings()` raises a clear error.

### `_build_ctx()` — read from config, not hardcoded

```python
# before
admin_peer_id="_admin",
admin_device_id="_admin",

# after
admin_peer_id=s.peer.peer_id,
admin_device_id=s.peer.device_id,
```

`LibraryCtx.admin_peer_id` and `admin_peer_id` are renamed to `peer_id` and `device_id`
to reflect that they are no longer exclusively about an admin identity.

### key path resolution

`_load_admin_key()` in `services/peers.py` and `_load_privkey()` in `services/sync.py`
both look up:

```
~/.config/scholartools/keys/{ctx.peer_id}/{ctx.device_id}.key
```

This is unchanged in structure — only the values change from hardcoded `_admin/_admin`
to whatever is in config.

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

`role` is already a field on `DeviceIdentity` (defaults to `"peer"`). This feat renames
`"peer"` to `"contributor"` in the model default and in `peer_register()` to make the
semantics explicit.

The admin role is determined by the peer directory entry, not by having a key named
`_admin`. `peer_register()`, `peer_add_device()`, and `peer_revoke()` load and verify the
caller's keypair (identified by `ctx.peer_id` / `ctx.device_id`), then check that the
caller's peer directory entry has `role == "admin"` before proceeding.

### bootstrap change

The `_admin/_admin` keypair concept is retired. Bootstrap is now:

1. `peer_init(peer_id, device_id)` — same as before, creates the keypair
2. `peer_register_self()` — NEW convenience function: self-signs a peer record with
   `role="admin"` for the first peer on a fresh deployment, without requiring a
   pre-existing admin key

`peer_register_self()` is only valid when the peer directory is empty. If the directory
already has entries, it returns an error — use `peer_register()` with an existing admin
peer instead.

### `bootstrap_identity.py` update

The script gains a `--role` flag (default: `contributor`; use `--role admin` for the
first peer on a new deployment) and writes the `peer` block to `config.json`
automatically after `peer_init`.

```bash
# first peer on a new deployment (admin)
uv run python scripts/bootstrap_identity.py \
  --peer-id sabhz --device-id laptop --role admin

# adding a second researcher (contributor)
uv run python scripts/bootstrap_identity.py \
  --peer-id elena --device-id desktop --role contributor
# → outputs the public key for the admin to register
```

### `remote-setup.md` update

Step 3 is simplified: one command, no manual `peer_register()` call for the first peer.
Section 7 (adding a second device) and a new section (adding a second researcher) are
updated to reflect the role model.

## what this does not change

- The `peers/` directory layout and Ed25519 signing protocol — unchanged
- `pull()` verification logic — unchanged; it still rejects unregistered peers
- The blob sync layer — `link_file`, `get_file`, `prefetch_blobs` — unchanged
- The public API surface — `push`, `pull`, `create_snapshot`, etc. — unchanged
- Existing local-only setups (no `sync` block) — unchanged; `peer` block is optional

## design decisions

**Role in peer directory, not in config.** The peer directory is the trust anchor —
it is signed by the admin and shared across peers via the bucket. Storing role in
`config.json` would let any peer self-promote. The directory entry is the authoritative
source.

**`peer_register_self()` instead of admin bootstrapping via `_admin` key.** The old
approach created a ghost identity (`_admin`) that had no correspondence to any real
researcher. Self-registration on an empty directory is the honest primitive: the first
peer simply declares themselves admin with no prior authority — which is exactly the
correct trust model for a new deployment.

**Rename `LibraryCtx.admin_peer_id` → `peer_id`.** The field was never exclusively about
admin peers; it was always "the peer signing on this machine." Renaming removes the
misleading implication.

**`"peer"` → `"contributor"` in DeviceIdentity.role.** "Peer" was ambiguous —
everything in the system is a peer. "Contributor" matches the mental model: someone who
contributes references but does not manage membership.

## out of scope

- Per-field or per-record access control (read ACLs) — S3 bucket policies are the
  appropriate layer for that
- Role elevation (contributor → admin) without a re-registration — out of scope;
  revoke and re-register with the new role
- Automatic role verification on push (i.e., rejecting contributor pushes that include
  peer directory mutations) — the peer directory is append-only via the public API;
  enforcement is implicit
