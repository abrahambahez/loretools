import base64
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scholartools.adapters.peer_directory import load_peer_directory
from scholartools.services.peers import (
    _canonical,
    _sign,
    _verify,
    make_pull_verifier,
    peer_add_device,
    peer_init,
    peer_register,
    peer_revoke,
    peer_revoke_device,
    verify_entry,
)


def _make_ctx(tmp_path: Path, admin_key_path: Path | None = None):
    from unittest.mock import MagicMock

    from scholartools.models import LibraryCtx

    ctx = MagicMock(spec=LibraryCtx)
    ctx.peers_dir = str(tmp_path / "peers")
    ctx.data_dir = str(tmp_path)
    ctx.admin_peer_id = "_admin"
    ctx.admin_device_id = "_admin"
    return ctx


# --- crypto primitives ---


def test_canonical_excludes_signature():
    record = {"peer_id": "a", "devices": [], "signature": "sig123"}
    result = _canonical(record)
    data = json.loads(result)
    assert "signature" not in data
    assert data["peer_id"] == "a"


def test_canonical_sorts_keys():
    record = {"z_key": 1, "a_key": 2}
    raw = _canonical(record)
    assert raw == b'{"a_key":2,"z_key":1}'


def test_sign_verify_roundtrip(tmp_path):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.generate()
    priv_bytes = priv.private_bytes_raw()
    pub_bytes = priv.public_key().public_bytes_raw()
    payload = b"test payload"
    sig = _sign(payload, priv_bytes)
    assert _verify(payload, sig, pub_bytes)


def test_verify_fails_wrong_payload(tmp_path):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.generate()
    priv_bytes = priv.private_bytes_raw()
    pub_bytes = priv.public_key().public_bytes_raw()
    sig = _sign(b"original", priv_bytes)
    assert not _verify(b"tampered", sig, pub_bytes)


def test_verify_fails_wrong_key():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.generate()
    other_priv = Ed25519PrivateKey.generate()
    sig = _sign(b"payload", priv.private_bytes_raw())
    assert not _verify(b"payload", sig, other_priv.public_key().public_bytes_raw())


# --- peer_init ---


@pytest.mark.asyncio
async def test_peer_init_creates_key(monkeypatch, tmp_path):
    keys_dir = tmp_path / "keys"
    monkeypatch.setattr(
        "scholartools.services.peers.CONFIG_PATH", tmp_path / "config.json"
    )
    ctx = _make_ctx(tmp_path)
    result = await peer_init("alice", "laptop", ctx)
    assert result.error is None
    assert result.identity is not None
    assert result.identity.peer_id == "alice"
    assert result.identity.device_id == "laptop"
    key_path = tmp_path / "keys" / "alice" / "laptop.key"
    assert key_path.exists()
    assert oct(key_path.stat().st_mode)[-3:] == "600"
    assert len(key_path.read_bytes()) == 32


@pytest.mark.asyncio
async def test_peer_init_rejects_duplicate(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "scholartools.services.peers.CONFIG_PATH", tmp_path / "config.json"
    )
    ctx = _make_ctx(tmp_path)
    await peer_init("alice", "laptop", ctx)
    result = await peer_init("alice", "laptop", ctx)
    assert result.error is not None
    assert "already exists" in result.error


# --- peer_register ---


@pytest.mark.asyncio
async def test_peer_register_no_admin_key(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "scholartools.services.peers.CONFIG_PATH", tmp_path / "config.json"
    )
    ctx = _make_ctx(tmp_path)
    from scholartools.models import PeerIdentity

    identity = PeerIdentity(peer_id="bob", device_id="desktop", public_key="AAAA")
    result = await peer_register(identity, ctx)
    assert result.error is not None
    assert "admin keypair not found" in result.error


@pytest.mark.asyncio
async def test_peer_register_admin_self(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "scholartools.services.peers.CONFIG_PATH", tmp_path / "config.json"
    )
    ctx = _make_ctx(tmp_path)
    init_result = await peer_init("_admin", "_admin", ctx)
    assert init_result.error is None
    result = await peer_register(init_result.identity, ctx)
    assert result.error is None
    assert result.peer_id == "_admin"
    record_path = Path(ctx.peers_dir) / "_admin"
    assert record_path.exists()
    data = json.loads(record_path.read_text())
    assert data["devices"][0]["role"] == "admin"
    assert data["signature"] is not None


@pytest.mark.asyncio
async def test_peer_register_registers_peer(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "scholartools.services.peers.CONFIG_PATH", tmp_path / "config.json"
    )
    ctx = _make_ctx(tmp_path)
    # Initialize and register admin first
    admin_init = await peer_init("_admin", "_admin", ctx)
    await peer_register(admin_init.identity, ctx)
    # Initialize peer key
    peer_init_result = await peer_init("alice", "laptop", ctx)
    result = await peer_register(peer_init_result.identity, ctx)
    assert result.error is None
    assert result.peer_id == "alice"
    record_path = Path(ctx.peers_dir) / "alice"
    data = json.loads(record_path.read_text())
    assert data["devices"][0]["role"] == "peer"


# --- load_peer_directory ---


def test_load_peer_directory_excludes_revoked(tmp_path):
    peers_dir = tmp_path / "peers"
    peers_dir.mkdir()
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    def _pub_b64(priv):
        return (
            base64.urlsafe_b64encode(priv.public_key().public_bytes_raw())
            .rstrip(b"=")
            .decode()
        )

    priv1 = Ed25519PrivateKey.generate()
    priv2 = Ed25519PrivateKey.generate()
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "peer_id": "alice",
        "devices": [
            {
                "device_id": "laptop",
                "public_key": _pub_b64(priv1),
                "registered_at": now,
                "revoked_at": None,
                "role": "peer",
            },
            {
                "device_id": "phone",
                "public_key": _pub_b64(priv2),
                "registered_at": now,
                "revoked_at": now,  # revoked
                "role": "peer",
            },
        ],
        "signature": "dummy",
    }
    (peers_dir / "alice").write_text(json.dumps(record), encoding="utf-8")
    peer_map = load_peer_directory(peers_dir)
    assert ("alice", "laptop") in peer_map
    assert ("alice", "phone") not in peer_map


def test_load_peer_directory_empty(tmp_path):
    assert load_peer_directory(tmp_path / "nonexistent") == {}


# --- verify_entry ---


def test_verify_entry_pass(tmp_path):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.generate()
    pub_bytes = priv.public_key().public_bytes_raw()
    entry = {"peer_id": "alice", "device_id": "laptop", "data": "hello"}
    payload = _canonical(entry)
    entry["signature"] = _sign(payload, priv.private_bytes_raw())
    peer_map = {("alice", "laptop"): pub_bytes}
    result = verify_entry(entry, peer_map)
    assert result.verified
    assert result.error is None


def test_verify_entry_unknown_peer():
    entry = {"peer_id": "unknown", "device_id": "dev", "signature": "sig"}
    result = verify_entry(entry, {})
    assert not result.verified
    assert "unknown peer" in result.error


def test_verify_entry_bad_signature():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.generate()
    pub_bytes = priv.public_key().public_bytes_raw()
    entry = {
        "peer_id": "alice",
        "device_id": "laptop",
        "data": "hello",
        "signature": "badsig",
    }
    peer_map = {("alice", "laptop"): pub_bytes}
    result = verify_entry(entry, peer_map)
    assert not result.verified


def test_verify_entry_missing_fields():
    result = verify_entry({"data": "no ids"}, {})
    assert not result.verified
    assert "missing" in result.error


# --- peer_revoke_device ---


@pytest.mark.asyncio
async def test_peer_revoke_device(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "scholartools.services.peers.CONFIG_PATH", tmp_path / "config.json"
    )
    ctx = _make_ctx(tmp_path)
    admin_init = await peer_init("_admin", "_admin", ctx)
    await peer_register(admin_init.identity, ctx)
    peer_init_result = await peer_init("alice", "laptop", ctx)
    await peer_register(peer_init_result.identity, ctx)
    result = await peer_revoke_device("alice", "laptop", ctx)
    assert result.revoked
    assert result.error is None
    record_data = json.loads((Path(ctx.peers_dir) / "alice").read_text())
    device = record_data["devices"][0]
    assert device["revoked_at"] is not None

    peer_map = load_peer_directory(Path(ctx.peers_dir))
    assert ("alice", "laptop") not in peer_map


# --- peer_revoke ---


@pytest.mark.asyncio
async def test_peer_revoke_all_devices(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "scholartools.services.peers.CONFIG_PATH", tmp_path / "config.json"
    )
    ctx = _make_ctx(tmp_path)
    admin_init = await peer_init("_admin", "_admin", ctx)
    await peer_register(admin_init.identity, ctx)
    peer_init_result = await peer_init("alice", "laptop", ctx)
    await peer_register(peer_init_result.identity, ctx)
    second_device = await peer_init("alice", "phone", ctx)
    await peer_add_device("alice", second_device.identity, ctx)
    result = await peer_revoke("alice", ctx)
    assert result.revoked
    record_data = json.loads((Path(ctx.peers_dir) / "alice").read_text())
    for device in record_data["devices"]:
        assert device["revoked_at"] is not None


# --- make_pull_verifier ---


def test_make_pull_verifier_pass(monkeypatch, tmp_path):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    peers_dir = tmp_path / "peers"
    peers_dir.mkdir()
    priv = Ed25519PrivateKey.generate()
    pub_bytes = priv.public_key().public_bytes_raw()
    pub_b64 = base64.urlsafe_b64encode(pub_bytes).rstrip(b"=").decode()
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "peer_id": "bob",
        "devices": [
            {
                "device_id": "pc",
                "public_key": pub_b64,
                "registered_at": now,
                "revoked_at": None,
                "role": "peer",
            }
        ],
        "signature": "dummy",
    }
    (peers_dir / "bob").write_text(json.dumps(record), encoding="utf-8")
    entry = {"peer_id": "bob", "device_id": "pc", "data": "change"}
    payload = _canonical(entry)
    entry["signature"] = _sign(payload, priv.private_bytes_raw())
    verifier = make_pull_verifier(peers_dir)
    result = verifier(entry)
    assert result.verified


def test_make_pull_verifier_writes_rejected(tmp_path):
    peers_dir = tmp_path / "peers"
    peers_dir.mkdir()
    entry = {"peer_id": "ghost", "device_id": "pc", "signature": "bad"}
    verifier = make_pull_verifier(peers_dir, data_dir=tmp_path)
    result = verifier(entry)
    assert not result.verified
    rejected_files = list((tmp_path / "rejected").iterdir())
    assert len(rejected_files) == 1
    stored = json.loads(rejected_files[0].read_text())
    assert stored["peer_id"] == "ghost"
