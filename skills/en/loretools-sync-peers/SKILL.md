---
name: loretools-sync-peers
description: loretools distributed sync, peer management, and blob operations — step-by-step setup guide for S3-backed sync, adding devices and collaborators, daily sync workflow, conflict resolution, peer lifecycle management, and fetching or prefetching file blobs from S3. Use this whenever the user asks about syncing their loretools library across devices, setting up a new device or collaborator, registering or revoking peers, handling sync conflicts, accessing a file that may not be cached locally, or bulk-fetching blobs before processing. Guide the user through the full journey even if they only mention one step.
---

Sync works by writing a cryptographically signed change log to an S3-compatible bucket. Every device reads each other's changes and verifies signatures — no central server, no trust required.

## Journey overview

1. [Get a bucket](#1-get-a-bucket)
2. [Configure this device](#2-configure-this-device)
3. [Initialize this device's identity](#3-initialize-this-devices-identity)
4. [Upload the first snapshot](#4-upload-the-first-snapshot)
5. [Daily sync workflow](#5-daily-sync-workflow)
6. [Add a second device (same researcher)](#6-add-a-second-device-same-researcher)
7. [Add a collaborator (different researcher)](#7-add-a-collaborator-different-researcher)
8. [Revoke access](#8-revoke-access)

---

## 1. Get a bucket

You need an S3-compatible object storage bucket. Any of these work:

| Provider | Notes |
|----------|-------|
| **AWS S3** | Standard. Set `endpoint` to `null`. |
| **Cloudflare R2** | No egress fees. Set `endpoint` to your R2 endpoint URL. |
| **Backblaze B2** | Cheap. Set `endpoint` to the B2 S3-compatible URL. |
| **MinIO** | Self-hosted. Set `endpoint` to your MinIO URL. |

From your provider, collect: **bucket name**, **access key**, **secret key**, and **endpoint URL** (null for AWS).

---

## 2. Configure this device

Edit `~/.config/loretools/config.json` (Windows: `C:\Users\<user>\.config\loretools\config.json`).

Add a `sync` block and a `peer` block. Choose any names for `peer_id` (who you are, e.g. `"alice"`) and `device_id` (this machine, e.g. `"laptop"`):

```json
{
  "sync": {
    "bucket": "my-loretools-bucket",
    "access_key": "YOUR_ACCESS_KEY",
    "secret_key": "YOUR_SECRET_KEY",
    "endpoint": null
  },
  "peer": {
    "peer_id": "alice",
    "device_id": "laptop"
  }
}
```

Changes take effect on the next `lore` command.

---

## 3. Initialize this device's identity

Run once per device. Generates an Ed25519 keypair so your changes can be signed and verified.

```sh
lore peers init alice laptop
# prints PeerIdentity JSON: {peer_id, device_id, public_key}

lore peers register-self
# Writes your public key into the local peers registry.
```

`peer_id` and `device_id` must match what you put in config.json.

---

## 4. Upload the first snapshot

Uploads a full copy of your library to the bucket. Other devices will bootstrap from this.

```sh
lore sync snapshot
```

Run once after initial setup, and again after major bulk imports.

---

## 5. Daily sync workflow

Always pull before pushing to apply any remote changes first.

```sh
lore sync pull    # apply remote changes
# ... make local edits (add/update/delete references) ...
lore sync push    # upload your change log entries to the bucket
```

After pulling, check for conflicts:

```sh
lore sync list-conflicts
# prints ConflictRecord list: uid, field, local_value, local_timestamp_hlc,
#                             remote_value, remote_timestamp_hlc, remote_peer_id

# Pick a winner for each conflict:
lore sync resolve-conflict <uid> <field> <local_value>    # keep local
lore sync resolve-conflict <uid> <field> <remote_value>   # keep remote
```

To recover a reference deleted by a remote peer:

```sh
lore sync restore <citekey>
```

---

## Blob management

File blobs (PDFs, EPUBs) are stored in S3 separately from the change log. Use these commands when working with files on a synced library.

```sh
lore files get <citekey>
# Returns file bytes. Fetches from S3 if not cached locally.

lore files prefetch [--citekeys key1,key2,...]
# Downloads blobs from S3 for the given citekeys (all if omitted).
# Run before bulk processing to avoid repeated S3 round-trips.
```

---

## 6. Add a second device (same researcher)

Use this to sync `alice`'s library to a new machine (e.g. `"desktop"`).

**On the new device:**

1. Edit config.json — same `peer_id`, new `device_id`:
   ```json
   { "peer": { "peer_id": "alice", "device_id": "desktop" } }
   ```
2. Generate a keypair and share the identity JSON with the first device:
   ```sh
   lore peers init alice desktop
   # copy the printed identity JSON
   ```

**On the first device (as admin):**

```sh
lore peers add-device alice '<identity-json>'
# or: echo '<identity-json>' | lore peers add-device alice
lore sync push    # publish the updated peer record to the bucket
```

**Back on the new device:**

```sh
lore peers register-self
lore sync pull    # bootstraps library from the snapshot + change log
```

---

## 7. Add a collaborator (different researcher)

Use this to give a different person (`"bob"`) access to the shared bucket.

**Bob, on his device:**

```sh
lore peers init bob bob-laptop
# copy the printed identity JSON
lore peers register-self
```

**Alice (admin), on her device:**

```sh
lore peers register '<bob-identity-json>'
# or: echo '<bob-identity-json>' | lore peers register
lore sync push    # publishes bob's peer record to the bucket
```

**Bob:**

```sh
lore sync pull    # bootstraps from the shared library
```

---

## 8. Revoke access

Revoke a single device (e.g. a lost laptop):

```sh
lore peers revoke-device alice laptop
lore sync push
```

Revoke an entire peer (removes all their devices):

```sh
lore peers revoke bob
lore sync push
```

Revoked devices are rejected at pull time on all other peers.

---

## CLI reference

```sh
# Identity
lore peers init <peer_id> <device_id>
lore peers register-self
lore peers register [<identity_json>|-]
lore peers add-device <peer_id> [<identity_json>|-]
lore peers revoke-device <peer_id> <device_id>
lore peers revoke <peer_id>

# Sync
lore sync push
lore sync pull
lore sync snapshot
lore sync list-conflicts
lore sync resolve-conflict <uid> <field> <value>
lore sync restore <citekey>

# Blobs
lore files get <citekey>
lore files prefetch [--citekeys key1,key2,...]
```
