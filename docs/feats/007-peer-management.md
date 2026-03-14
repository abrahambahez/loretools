# 007: peer management — identity, key management, and pull verification

## context

The full design is specified in `docs/feats/007-peer-mamagement` (the original RFC).
This feat covers what changes in the codebase to implement it: new models, service
functions, adapter, and the verification hook on pull.

Requires `cryptography` (PyCA) as a new dependency — approved before adding to
`pyproject.toml`.

## what changes

### new models (`models.py`)

```python
class DeviceIdentity(BaseModel):
    device_id: str
    public_key: str          # base64url Ed25519 public key
    registered_at: datetime
    revoked_at: datetime | None = None

class PeerRecord(BaseModel):
    peer_id: str
    devices: list[DeviceIdentity]
    registered_at: datetime
    revoked_at: datetime | None = None
    role: str = "peer"       # "admin" for the _admin record
    signature: str           # base64url Ed25519 signature

class PeerIdentity(BaseModel):
    peer_id: str
    device: DeviceIdentity
```

### key storage (`config.py` / `Settings`)

Private keys live at `~/.config/scholartools/keys/{peer_id}/{device_id}.key`
(mode `0600`), public keys at the same path with `.pub`. Path derived from
`CONFIG_PATH.parent / "keys"` — never from `data_dir`.

### peer service (`services/peers.py`)

New module with these async functions (all take `ctx: LibraryCtx`):

- `peer_init(peer_id, device_id)` — generates Ed25519 keypair, stores private key,
  returns `PeerIdentity`.
- `peer_register(identity)` — admin only. Signs and writes `peers/{peer_id}` to
  shared storage.
- `peer_add_device(peer_id, device_identity)` — admin only. Appends device entry,
  re-signs, writes.
- `peer_revoke_device(peer_id, device_id)` — admin only. Sets `revoked_at`, re-signs.
- `peer_revoke(peer_id)` — admin only. Sets `revoked_at` on all devices, re-signs.

Canonical payload for signing: record JSON with `signature` excluded, sorted keys,
no extra whitespace.

Admin functions verify local keypair matches `_admin` record before writing; return
an error result otherwise.

### peer directory adapter (`adapters/peer_directory.py`)

New module with functions to read/write the `peers/` directory through the existing
`RemoteSyncPort`. Builds the `(peer_id, device_id) → public_key` map used during pull.

### pull verification (`adapters/sync_composite.py`)

Pull loads the full `peers/` directory at session start (never cached between sessions),
then applies these rules to each change log entry before merge:

1. `(peer_id, device_id)` must exist in the directory.
2. The pair must not have `revoked_at` set.
3. Signature must verify against the registered Ed25519 public key.

Entries failing any rule are written to `rejected/{hlc_timestamp}-{peer_id}-{device_id}.json`
and never applied. Rejections are surfaced in the `pull()` return value.

### public API (`__init__.py`)

Five new sync wrappers: `peer_init`, `peer_register`, `peer_add_device`,
`peer_revoke_device`, `peer_revoke`.

## out of scope

- Storage credential revocation (S3 IAM, SSH keys) — coordinator responsibility, out of band.
- Admin key backup — coordinator responsibility.
- Entry confidentiality — signatures provide integrity/attribution only.
- Secondary admin support — deferred.
- Snapshot signing — deferred to sync phase 2.
