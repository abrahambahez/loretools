import json
from unittest.mock import patch

import pytest

from scholartools.cli import _build_parser
from scholartools.models import (
    PeerAddDeviceResult,
    PeerIdentity,
    PeerInitResult,
    PeerRegisterResult,
    PeerRevokeDeviceResult,
    PeerRevokeResult,
    Result,
)


def _run(argv):
    parser = _build_parser()
    args = parser.parse_args(argv)
    args.func(args)


_IDENTITY_JSON = '{"peer_id":"p1","device_id":"d1","public_key":"abc"}'
_IDENTITY = PeerIdentity(peer_id="p1", device_id="d1", public_key="abc")


def test_peers_init_calls_peer_init():
    result = PeerInitResult(identity=_IDENTITY)
    with patch("scholartools.peer_init", return_value=result) as mock:
        with pytest.raises(SystemExit) as exc_info:
            _run(["peers", "init", "peer1", "device1"])
        assert exc_info.value.code == 0
        mock.assert_called_once_with("peer1", "device1")


def test_peers_register_calls_peer_register():
    result = PeerRegisterResult(peer_id="p1")
    with patch("scholartools.peer_register", return_value=result) as mock:
        with pytest.raises(SystemExit) as exc_info:
            _run(["peers", "register", _IDENTITY_JSON])
        assert exc_info.value.code == 0
        mock.assert_called_once_with(_IDENTITY)


def test_peers_add_device_calls_peer_add_device():
    result = PeerAddDeviceResult(peer_id="p1")
    with patch("scholartools.peer_add_device", return_value=result) as mock:
        with pytest.raises(SystemExit) as exc_info:
            _run(["peers", "add-device", "peer1", _IDENTITY_JSON])
        assert exc_info.value.code == 0
        mock.assert_called_once_with("peer1", _IDENTITY)


def test_peers_revoke_device_calls_peer_revoke_device():
    result = PeerRevokeDeviceResult(revoked=True)
    with patch("scholartools.peer_revoke_device", return_value=result) as mock:
        with pytest.raises(SystemExit) as exc_info:
            _run(["peers", "revoke-device", "peer1", "device1"])
        assert exc_info.value.code == 0
        mock.assert_called_once_with("peer1", "device1")


def test_peers_revoke_calls_peer_revoke():
    result = PeerRevokeResult(revoked=True)
    with patch("scholartools.peer_revoke", return_value=result) as mock:
        with pytest.raises(SystemExit) as exc_info:
            _run(["peers", "revoke", "peer1"])
        assert exc_info.value.code == 0
        mock.assert_called_once_with("peer1")


def test_peers_register_self_calls_peer_register_self():
    result = Result(ok=True)
    with patch("scholartools.peer_register_self", return_value=result) as mock:
        with pytest.raises(SystemExit) as exc_info:
            _run(["peers", "register-self"])
        assert exc_info.value.code == 0
        mock.assert_called_once_with()


def test_peers_register_invalid_json_exits_1(capsys):
    with pytest.raises(SystemExit) as exc_info:
        _run(["peers", "register", "{invalid}"])
    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["ok"] is False
    assert data["error"] is not None
