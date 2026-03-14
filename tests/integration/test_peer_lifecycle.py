import json
from pathlib import Path

import pytest

from scholartools.adapters.peer_directory import load_peer_directory
from scholartools.services.peers import (
    _canonical,
    _sign,
    make_pull_verifier,
    peer_add_device,
    peer_init,
    peer_register,
    peer_revoke_device,
    verify_entry,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_peer_lifecycle(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "scholartools.services.peers.CONFIG_PATH", tmp_path / "config.json"
    )
    from unittest.mock import MagicMock

    from scholartools.models import LibraryCtx

    ctx = MagicMock(spec=LibraryCtx)
    ctx.peers_dir = str(tmp_path / "peers")
    ctx.data_dir = str(tmp_path)
    ctx.admin_peer_id = "_admin"
    ctx.admin_device_id = "_admin"

    # 1. Admin init + register (self-signed)
    admin_init = await peer_init("_admin", "_admin", ctx)
    assert admin_init.error is None
    admin_reg = await peer_register(admin_init.identity, ctx)
    assert admin_reg.error is None

    admin_record = json.loads((Path(ctx.peers_dir) / "_admin").read_text())
    assert admin_record["devices"][0]["role"] == "admin"

    # 2. Register a peer
    peer_init_r = await peer_init("alice", "laptop", ctx)
    assert peer_init_r.error is None
    reg_r = await peer_register(peer_init_r.identity, ctx)
    assert reg_r.error is None

    # 3. Add a second device
    device2 = await peer_init("alice", "phone", ctx)
    add_r = await peer_add_device("alice", device2.identity, ctx)
    assert add_r.error is None

    alice_record = json.loads((Path(ctx.peers_dir) / "alice").read_text())
    assert len(alice_record["devices"]) == 2

    # 4. Verify a signed entry from alice/laptop
    peer_map = load_peer_directory(Path(ctx.peers_dir))
    assert ("alice", "laptop") in peer_map
    assert ("alice", "phone") in peer_map

    key_bytes = (tmp_path / "keys" / "alice" / "laptop.key").read_bytes()
    entry = {"peer_id": "alice", "device_id": "laptop", "action": "add", "ref": "x"}
    payload = _canonical(entry)
    entry["signature"] = _sign(payload, key_bytes)
    verify_r = verify_entry(entry, peer_map)
    assert verify_r.verified

    # 5. Revoke alice/phone device
    rev_r = await peer_revoke_device("alice", "phone", ctx)
    assert rev_r.revoked

    peer_map2 = load_peer_directory(Path(ctx.peers_dir))
    assert ("alice", "laptop") in peer_map2
    assert ("alice", "phone") not in peer_map2

    # 6. Verify rejected entry is written
    bad_entry = {"peer_id": "ghost", "device_id": "pc", "signature": "bad"}
    verifier = make_pull_verifier(Path(ctx.peers_dir), data_dir=tmp_path)
    bad_r = verifier(bad_entry)
    assert not bad_r.verified
    rejected = list((tmp_path / "rejected").iterdir())
    assert len(rejected) == 1
