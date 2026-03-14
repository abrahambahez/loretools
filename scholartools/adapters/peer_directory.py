import base64
import json
from pathlib import Path


def load_peer_directory(peers_dir: Path) -> dict[tuple[str, str], bytes]:
    result: dict[tuple[str, str], bytes] = {}
    if not peers_dir.exists():
        return result
    for f in peers_dir.iterdir():
        if not f.is_file():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        peer_id = data.get("peer_id", "")
        for device in data.get("devices", []):
            if device.get("revoked_at"):
                continue
            device_id = device.get("device_id", "")
            pub_b64 = device.get("public_key", "")
            padded = pub_b64 + "=" * (-len(pub_b64) % 4)
            try:
                result[(peer_id, device_id)] = base64.urlsafe_b64decode(padded)
            except ValueError:
                continue
    return result
