import hashlib
from pathlib import Path


def compute_sha256_streaming(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def blob_cache_path(data_dir: Path, sha256: str, ext: str = "") -> Path:
    return data_dir / "blob_cache" / f"{sha256}{ext}"


def ensure_blob_cache_dir(data_dir: Path) -> None:
    (data_dir / "blob_cache").mkdir(parents=True, exist_ok=True)
