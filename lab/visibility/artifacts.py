"""Bound local proof storage without deleting existing evidence."""

from contextlib import contextmanager
import fcntl
import os
from pathlib import Path

MAX_RUNS = 20
MAX_BYTES = 128 * 1024 * 1024
RESERVED_RUN_BYTES = 20 * 1024 * 1024


@contextmanager
def proof_lock(root: Path):
    """Serialize both proof runners so their storage reservations cannot race."""
    folder = root / "artifacts"
    if folder.is_symlink():
        raise ValueError("Proof storage must not be a symbolic link")
    folder.mkdir(exist_ok=True)
    descriptor = os.open(folder / ".lab.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another lab proof is running; wait for it to finish") from exc
        yield


def reserve(root: Path, name: str) -> Path:
    folder = root / "artifacts" / "lab"
    if folder.is_symlink() or (root / "artifacts").is_symlink():
        raise ValueError("Proof storage must not be a symbolic link")
    folder.mkdir(parents=True, exist_ok=True)
    runs = list(folder.iterdir())
    if len(runs) >= MAX_RUNS:
        raise ValueError("Proof storage reached 20 entries; archive or remove old evidence explicitly")
    total = 0
    for path in folder.rglob("*"):
        if path.is_symlink():
            raise ValueError("Proof storage contains a symbolic link")
        if path.is_file():
            total += path.stat().st_size
    if total + RESERVED_RUN_BYTES > MAX_BYTES:
        raise ValueError("Proof storage lacks the 20 MiB reserve within its 128 MiB budget")
    result = folder / name
    result.mkdir(exist_ok=False)
    return result
