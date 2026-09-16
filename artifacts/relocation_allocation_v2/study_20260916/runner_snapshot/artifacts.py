"""Lossless, streaming case artifacts with legacy JSON reader compatibility."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile


COMPRESSION_LEVEL = 3
WRITE_CHUNK_BYTES = 1024 * 1024


def resolve_json(path: Path) -> Path:
    """Resolve saved JSON and gzip JSON without rewriting historical artifacts."""
    path = Path(path)
    if path.is_file():
        return path
    alternate = Path(str(path)[:-3]) if path.suffix == ".gz" else Path(str(path) + ".gz")
    return alternate if alternate.is_file() else path


def read_json(path: Path):
    path = resolve_json(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def case_artifacts(folder: Path) -> list[Path]:
    """List one artifact per case, accepting old and new result directories."""
    paths = {path.name: path for path in Path(folder).glob("case_*.json")}
    for path in Path(folder).glob("case_*.json.gz"):
        paths.setdefault(path.name[:-3], path)
    return [paths[name] for name in sorted(paths)]


def write_compressed_json(path: Path, value) -> Path:
    """Serialize directly into gzip, verify every byte, then publish atomically.

    Only this call's incomplete temporary file is removed on interruption. No
    uncompressed trace is written, and an existing immutable artifact is never
    replaced. The simulator's per-case object remains unchanged. Actual I/O
    failures propagate to the caller.
    """
    path = Path(path)
    if not str(path).endswith(".json.gz"):
        path = Path(str(path) + ".gz")
    temporary = None

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise FileExistsError(f"Completed artifact already exists: {path}")
        digest = hashlib.sha256()
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent,
                                         prefix=f".{path.name}.", suffix=".tmp", delete=False) as raw:
            temporary = Path(raw.name)
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw,
                               compresslevel=COMPRESSION_LEVEL, mtime=0) as compressed:
                buffer = bytearray()

                def flush_chunk():
                    digest.update(buffer)
                    compressed.write(buffer)
                    buffer.clear()

                encoder = json.JSONEncoder(allow_nan=False, separators=(",", ":"))
                for chunk in encoder.iterencode(value):
                    # A single long string can be larger than our write chunk.
                    encoded = chunk.encode("utf-8")
                    start = 0
                    while start < len(encoded):
                        count = min(WRITE_CHUNK_BYTES - len(buffer), len(encoded) - start)
                        buffer.extend(encoded[start:start + count])
                        start += count
                        if len(buffer) == WRITE_CHUNK_BYTES:
                            flush_chunk()
                buffer.extend(b"\n")
                if buffer:
                    flush_chunk()
            raw.flush()
            os.fsync(raw.fileno())
        verified = hashlib.sha256()
        with gzip.open(temporary, "rb") as stream:
            while chunk := stream.read(WRITE_CHUNK_BYTES):
                verified.update(chunk)
        if verified.digest() != digest.digest():
            raise IOError(f"Lossless compression verification failed for {path}")
        temporary.replace(path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return path
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
