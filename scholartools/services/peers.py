import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from scholartools.adapters.peer_directory import load_peer_directory
from scholartools.config import CONFIG_PATH
from scholartools.models import (
    DeviceIdentity,
    LibraryCtx,
    PeerAddDeviceResult,
    PeerIdentity,
    PeerInitResult,
    PeerRecord,
    PeerRegisterResult,
    PeerRevokeDeviceResult,
    PeerRevokeResult,
    VerifyEntryResult,
)


def _canonical(record: dict) -> bytes:
    data = {k: v for k, v in record.items() if k != "signature"}
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


def _sign(payload: bytes, private_key_bytes: bytes) -> str:
    key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    sig = key.sign(payload)
    return base64.urlsafe_b64encode(sig).rstrip(b"=").decode()


def _verify(payload: bytes, signature: str, public_key_bytes: bytes) -> bool:
    try:
        padded = signature + "=" * (-len(signature) % 4)
        sig_bytes = base64.urlsafe_b64decode(padded)
        key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        key.verify(sig_bytes, payload)
        return True
    except (InvalidSignature, ValueError):
        return False


def _load_admin_key(ctx: LibraryCtx) -> bytes | None:
    key_path = (
        CONFIG_PATH.parent / "keys" / ctx.admin_peer_id / f"{ctx.admin_device_id}.key"
    )
    return key_path.read_bytes() if key_path.exists() else None


def _admin_key_matches_record(
    admin_private_bytes: bytes,
    peers_dir: Path,
    admin_peer_id: str,
    admin_device_id: str,
) -> bool:
    record_path = peers_dir / admin_peer_id
    if not record_path.exists():
        return True
    try:
        data = json.loads(record_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    device = next(
        (d for d in data.get("devices", []) if d["device_id"] == admin_device_id),
        None,
    )
    if not device:
        return False
    priv = Ed25519PrivateKey.from_private_bytes(admin_private_bytes)
    expected = (
        base64.urlsafe_b64encode(priv.public_key().public_bytes_raw())
        .rstrip(b"=")
        .decode()
    )
    return expected == device["public_key"]


async def peer_init(peer_id: str, device_id: str, ctx: LibraryCtx) -> PeerInitResult:
    key_path = CONFIG_PATH.parent / "keys" / peer_id / f"{device_id}.key"
    if key_path.exists():
        return PeerInitResult(error=f"key already exists for {peer_id}/{device_id}")
    private_key = Ed25519PrivateKey.generate()
    pub_bytes = private_key.public_key().public_bytes_raw()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_bytes(private_key.private_bytes_raw())
    key_path.chmod(0o600)
    pub_b64 = base64.urlsafe_b64encode(pub_bytes).rstrip(b"=").decode()
    return PeerInitResult(
        identity=PeerIdentity(peer_id=peer_id, device_id=device_id, public_key=pub_b64)
    )


async def peer_register(identity: PeerIdentity, ctx: LibraryCtx) -> PeerRegisterResult:
    if not ctx.peers_dir:
        return PeerRegisterResult(error="peers_dir not configured in context")
    peers_dir = Path(ctx.peers_dir)
    admin_private_bytes = _load_admin_key(ctx)
    if admin_private_bytes is None:
        return PeerRegisterResult(error="admin keypair not found")
    if not _admin_key_matches_record(
        admin_private_bytes, peers_dir, ctx.admin_peer_id, ctx.admin_device_id
    ):
        return PeerRegisterResult(
            error="admin keypair does not match registered admin record"
        )
    is_admin_self = (
        identity.peer_id == ctx.admin_peer_id
        and identity.device_id == ctx.admin_device_id
    )
    now = datetime.now(timezone.utc)
    device = DeviceIdentity(
        device_id=identity.device_id,
        public_key=identity.public_key,
        registered_at=now,
        role="admin" if is_admin_self else "peer",
    )
    record = PeerRecord(peer_id=identity.peer_id, devices=[device])
    record_dict = json.loads(record.model_dump_json())
    record_dict.pop("signature", None)
    payload = _canonical(record_dict)
    record_dict["signature"] = _sign(payload, admin_private_bytes)
    peers_dir.mkdir(parents=True, exist_ok=True)
    (peers_dir / identity.peer_id).write_text(
        json.dumps(record_dict, ensure_ascii=False), encoding="utf-8"
    )
    return PeerRegisterResult(peer_id=identity.peer_id)


async def peer_add_device(
    peer_id: str, device_identity: PeerIdentity, ctx: LibraryCtx
) -> PeerAddDeviceResult:
    if not ctx.peers_dir:
        return PeerAddDeviceResult(error="peers_dir not configured in context")
    peers_dir = Path(ctx.peers_dir)
    admin_private_bytes = _load_admin_key(ctx)
    if admin_private_bytes is None:
        return PeerAddDeviceResult(error="admin keypair not found")
    if not _admin_key_matches_record(
        admin_private_bytes, peers_dir, ctx.admin_peer_id, ctx.admin_device_id
    ):
        return PeerAddDeviceResult(
            error="admin keypair does not match registered admin record"
        )
    record_path = peers_dir / peer_id
    if not record_path.exists():
        return PeerAddDeviceResult(error=f"peer {peer_id} not found")
    record_dict = json.loads(record_path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    new_device = DeviceIdentity(
        device_id=device_identity.device_id,
        public_key=device_identity.public_key,
        registered_at=now,
    )
    record_dict["devices"].append(json.loads(new_device.model_dump_json()))
    record_dict.pop("signature", None)
    payload = _canonical(record_dict)
    record_dict["signature"] = _sign(payload, admin_private_bytes)
    record_path.write_text(
        json.dumps(record_dict, ensure_ascii=False), encoding="utf-8"
    )
    return PeerAddDeviceResult(peer_id=peer_id)


async def peer_revoke_device(
    peer_id: str, device_id: str, ctx: LibraryCtx
) -> PeerRevokeDeviceResult:
    if not ctx.peers_dir:
        return PeerRevokeDeviceResult(error="peers_dir not configured in context")
    peers_dir = Path(ctx.peers_dir)
    admin_private_bytes = _load_admin_key(ctx)
    if admin_private_bytes is None:
        return PeerRevokeDeviceResult(error="admin keypair not found")
    if not _admin_key_matches_record(
        admin_private_bytes, peers_dir, ctx.admin_peer_id, ctx.admin_device_id
    ):
        return PeerRevokeDeviceResult(
            error="admin keypair does not match registered admin record"
        )
    record_path = peers_dir / peer_id
    if not record_path.exists():
        return PeerRevokeDeviceResult(error=f"peer {peer_id} not found")
    record_dict = json.loads(record_path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat()
    found = False
    for device in record_dict.get("devices", []):
        if device["device_id"] == device_id:
            device["revoked_at"] = now
            found = True
    if not found:
        return PeerRevokeDeviceResult(
            error=f"device {device_id} not found in peer {peer_id}"
        )
    record_dict.pop("signature", None)
    payload = _canonical(record_dict)
    record_dict["signature"] = _sign(payload, admin_private_bytes)
    record_path.write_text(
        json.dumps(record_dict, ensure_ascii=False), encoding="utf-8"
    )
    return PeerRevokeDeviceResult(revoked=True)


async def peer_revoke(peer_id: str, ctx: LibraryCtx) -> PeerRevokeResult:
    if not ctx.peers_dir:
        return PeerRevokeResult(error="peers_dir not configured in context")
    peers_dir = Path(ctx.peers_dir)
    admin_private_bytes = _load_admin_key(ctx)
    if admin_private_bytes is None:
        return PeerRevokeResult(error="admin keypair not found")
    if not _admin_key_matches_record(
        admin_private_bytes, peers_dir, ctx.admin_peer_id, ctx.admin_device_id
    ):
        return PeerRevokeResult(
            error="admin keypair does not match registered admin record"
        )
    record_path = peers_dir / peer_id
    if not record_path.exists():
        return PeerRevokeResult(error=f"peer {peer_id} not found")
    record_dict = json.loads(record_path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat()
    for device in record_dict.get("devices", []):
        device["revoked_at"] = now
    record_dict.pop("signature", None)
    payload = _canonical(record_dict)
    record_dict["signature"] = _sign(payload, admin_private_bytes)
    record_path.write_text(
        json.dumps(record_dict, ensure_ascii=False), encoding="utf-8"
    )
    return PeerRevokeResult(revoked=True)


def verify_entry(
    entry: dict, peer_map: dict[tuple[str, str], bytes]
) -> VerifyEntryResult:
    peer_id = entry.get("peer_id")
    device_id = entry.get("device_id")
    signature = entry.get("signature")
    if not peer_id or not device_id:
        return VerifyEntryResult(error="entry missing peer_id or device_id")
    pub_bytes = peer_map.get((peer_id, device_id))
    if pub_bytes is None:
        return VerifyEntryResult(error=f"unknown peer ({peer_id}, {device_id})")
    if not signature:
        return VerifyEntryResult(error="entry missing signature")
    payload = _canonical(entry)
    if not _verify(payload, signature, pub_bytes):
        return VerifyEntryResult(error="signature verification failed")
    return VerifyEntryResult(verified=True)


def make_pull_verifier(
    peers_dir: Path, data_dir: Path | None = None
) -> Callable[[dict], VerifyEntryResult]:
    def verify(entry: dict) -> VerifyEntryResult:
        peer_map = load_peer_directory(peers_dir)
        result = verify_entry(entry, peer_map)
        if not result.verified and data_dir is not None:
            peer_id = entry.get("peer_id", "unknown")
            device_id = entry.get("device_id", "unknown")
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            rejected_dir = data_dir / "rejected"
            rejected_dir.mkdir(parents=True, exist_ok=True)
            fname = f"{ts}-{peer_id}-{device_id}.json"
            (rejected_dir / fname).write_text(
                json.dumps(entry, ensure_ascii=False), encoding="utf-8"
            )
        return result

    return verify
