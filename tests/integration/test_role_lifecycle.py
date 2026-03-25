"""Integration test: two-researcher sync with role enforcement."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scholartools.models import ChangeLogEntry, LibraryCtx
from scholartools.services.peers import (
    peer_init,
    peer_register,
    peer_register_self,
)
from scholartools.services.sync import _change_log_entries, _write_change_log_entry


def _make_ctx(tmp_path: Path, peer_id: str, device_id: str, peers_dir: Path):
    ctx = MagicMock(spec=LibraryCtx)
    ctx.peers_dir = str(peers_dir)
    ctx.data_dir = str(tmp_path / peer_id)
    ctx.peer_id = peer_id
    ctx.device_id = device_id
    ctx.sync_config = None
    return ctx


@pytest.mark.integration
@pytest.mark.asyncio
async def test_role_lifecycle(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    shared_peers = tmp_path / "shared_peers"

    # peer-A is admin
    ctx_a = _make_ctx(tmp_path, "peer-a", "dev-a", shared_peers)
    (tmp_path / "peer-a").mkdir()
    await peer_init("peer-a", "dev-a", ctx_a)
    reg_self = await peer_register_self(ctx_a)
    assert reg_self.ok

    # peer-B is contributor
    ctx_b = _make_ctx(tmp_path, "peer-b", "dev-b", shared_peers)
    (tmp_path / "peer-b").mkdir()
    b_init = await peer_init("peer-b", "dev-b", ctx_b)
    assert b_init.error is None

    # peer-A registers peer-B
    reg_b = await peer_register(b_init.identity, ctx_a)
    assert reg_b.error is None
    b_record = json.loads((shared_peers / "peer-b").read_text())
    assert b_record["devices"][0]["role"] == "contributor"

    # push entries go to correct prefixes
    from scholartools.services.hlc import now as hlc_now

    ts_a = hlc_now("peer-a")
    entry_a = ChangeLogEntry(
        op="add_reference",
        uid="uid-a",
        uid_confidence="authoritative",
        citekey="ref-a",
        data={"title": "A"},
        peer_id="peer-a",
        device_id="dev-a",
        timestamp_hlc=ts_a,
        signature="",
    )
    _write_change_log_entry(Path(ctx_a.data_dir), entry_a)

    ts_b = hlc_now("peer-b")
    entry_b = ChangeLogEntry(
        op="add_reference",
        uid="uid-b",
        uid_confidence="authoritative",
        citekey="ref-b",
        data={"title": "B"},
        peer_id="peer-b",
        device_id="dev-b",
        timestamp_hlc=ts_b,
        signature="",
    )
    _write_change_log_entry(Path(ctx_b.data_dir), entry_b)

    entries_a = _change_log_entries(Path(ctx_a.data_dir), "")
    assert len(entries_a) == 1
    assert entries_a[0][1].peer_id == "peer-a"

    entries_b = _change_log_entries(Path(ctx_b.data_dir), "")
    assert len(entries_b) == 1
    assert entries_b[0][1].peer_id == "peer-b"

    # peer-B cannot call peer_register (not admin)
    from scholartools.models import PeerIdentity

    dummy_identity = PeerIdentity(peer_id="ghost", device_id="pc", public_key="AAAA")
    blocked = await peer_register(dummy_identity, ctx_b)
    assert blocked.error is not None
    assert "caller is not an admin" in blocked.error
