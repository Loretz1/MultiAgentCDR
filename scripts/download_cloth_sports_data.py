"""Resume and verify the four official Amazon2014 Cloth/Sports source files."""
from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import json
import os
from pathlib import Path
import threading
import time
from datetime import datetime, timezone

import requests

DOMAINS = ("Clothing_Shoes_and_Jewelry", "Sports_and_Outdoors")
BASE = "https://snap.stanford.edu/data/amazon/productGraph/categoryFiles/"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class Progress:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.started = time.monotonic()
        self.last_write = 0.0
        self.data = {"state": "running", "started_at": utc_now(), "files": {}}

    def write(self, force=False):
        with self.lock:
            now = time.monotonic()
            if not force and now - self.last_write < 2:
                return
            files = self.data["files"].values()
            received = sum(v.get("received_bytes", 0) for v in files)
            total = sum(v.get("expected_bytes", 0) for v in files)
            elapsed = now - self.started
            transferred = sum(v.get("network_bytes", 0) for v in files)
            speed = transferred / elapsed if elapsed else 0
            self.data.update(updated_at=utc_now(), elapsed_seconds=round(elapsed, 2),
                             received_bytes=received, expected_bytes=total,
                             network_bytes=transferred, bytes_per_second=round(speed),
                             download_eta_seconds=round(max(0, total-received)/speed) if speed else None)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp, self.path)
            self.last_write = now

    def update(self, filename, **values):
        with self.lock:
            self.data["files"].setdefault(filename, {}).update(values)
            self.write()


def verify(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    # Reading to EOF verifies every gzip member's CRC and uncompressed size.
    with gzip.open(path, "rb") as stream:
        while stream.read(8 * 1024 * 1024):
            pass
    return digest.hexdigest()


def download_one(domain, kind, root, progress, direct=False, max_attempts=5):
    filename = f"{kind}_{domain}{'_5' if kind == 'reviews' else ''}.json.gz"
    destination = root / "Amazon2014" / domain / "raw" / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    url = BASE + filename
    transferred = 0
    progress.update(filename, state="connecting", url=url, path=str(destination), network_bytes=0)
    with requests.Session() as session:
        if direct:
            session.trust_env = False
        session.headers["Accept-Encoding"] = "identity"
        for attempt in range(1, max_attempts + 1):
            try:
                head = session.head(url, timeout=(15, 30), allow_redirects=True)
                head.raise_for_status()
                expected = int(head.headers["Content-Length"])
                progress.update(filename, expected_bytes=expected, attempt=attempt)
                if destination.exists():
                    if destination.stat().st_size != expected:
                        raise RuntimeError(f"Existing final file has unexpected size: {destination}")
                    progress.update(filename, state="verifying", received_bytes=expected)
                    sha = verify(destination)
                    progress.update(filename, state="complete", sha256=sha, completed_at=utc_now())
                    print(f"Verified existing {filename}: {expected} bytes", flush=True)
                    return
                offset = partial.stat().st_size if partial.exists() else 0
                if offset > expected:
                    raise RuntimeError(f"Partial file exceeds expected size: {partial}")
                if offset < expected:
                    headers = {"Range": f"bytes={offset}-"} if offset else {}
                    with session.get(url, headers=headers, stream=True, timeout=(15, 90)) as response:
                        response.raise_for_status()
                        if offset and response.status_code == 206:
                            prefix = f"bytes {offset}-"
                            if not response.headers.get("Content-Range", "").startswith(prefix):
                                raise RuntimeError("Server returned a mismatched resume range")
                            mode = "ab"
                        elif response.status_code == 200:
                            offset, mode = 0, "wb"
                        else:
                            raise RuntimeError(f"Unexpected download response: {response.status_code}")
                        progress.update(filename, state="downloading", received_bytes=offset, error=None)
                        print(f"Downloading {filename} from {offset}/{expected} bytes", flush=True)
                        with partial.open(mode) as stream:
                            for chunk in response.iter_content(256 * 1024):
                                if chunk:
                                    stream.write(chunk)
                                    offset += len(chunk)
                                    transferred += len(chunk)
                                    progress.update(filename, received_bytes=offset, network_bytes=transferred)
                if partial.stat().st_size != expected:
                    raise RuntimeError(f"Incomplete download: {filename}")
                progress.update(filename, state="verifying", received_bytes=expected)
                try:
                    sha = verify(partial)
                except (gzip.BadGzipFile, EOFError, OSError):
                    # Preserve a corrupt download for inspection; the next attempt starts cleanly.
                    partial.rename(partial.with_name(partial.name + f".corrupt-{time.time_ns()}"))
                    raise
                os.replace(partial, destination)
                progress.update(filename, state="complete", sha256=sha, completed_at=utc_now(), error=None)
                progress.write(force=True)
                print(f"Complete {filename}: {expected} bytes, SHA256 {sha}", flush=True)
                return
            except Exception as exc:
                progress.update(filename, state="retrying" if attempt < max_attempts else "failed", error=str(exc))
                progress.write(force=True)
                print(f"Attempt {attempt} failed for {filename}: {exc}", flush=True)
                if attempt == max_attempts:
                    raise
                time.sleep(min(2 ** attempt, 15))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--status", type=Path, required=True)
    parser.add_argument("--direct", action="store_true", help="Ignore environment proxy settings for these downloads.")
    parser.add_argument("--max-attempts", type=int, default=5)
    args = parser.parse_args()
    if args.max_attempts < 1:
        parser.error("--max-attempts must be positive")
    args.status.parent.mkdir(parents=True, exist_ok=True)
    progress = Progress(args.status)
    progress.data["connection_mode"] = "direct" if args.direct else "environment"
    progress.write(force=True)
    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(download_one, d, k, args.data_root, progress, args.direct, args.max_attempts)
                   for d in DOMAINS for k in ("reviews", "meta")]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                errors.append(str(exc))
    progress.data.update(state="failed" if errors else "complete", errors=errors, finished_at=utc_now())
    progress.write(force=True)
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
