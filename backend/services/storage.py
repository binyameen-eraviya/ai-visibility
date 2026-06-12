"""Raw scrape storage.

Captured answers and screenshots are written behind a small interface so the
backing store can move from local disk to S3 (or similar) later without
touching the scrape runner or the read endpoints.

On-disk layout (see README):
    {storage_dir}/{project_id}/{YYYY-MM-DD}/{run_id}.json   # raw capture
    {storage_dir}/{project_id}/{YYYY-MM-DD}/{run_id}.png    # screenshot
"""

import os
import json
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_STORAGE_DIR = "/app/storage/scrapes"


class BaseStorageService(ABC):
    """Interface every storage backend implements."""

    @abstractmethod
    async def save_raw(self, project_id, run_id, data: dict) -> str:
        """Persist the raw capture for one run; return the storage path/key."""
        raise NotImplementedError

    @abstractmethod
    async def save_screenshot(self, project_id, run_id, image_bytes: bytes) -> str:
        """Persist a screenshot for one run; return the storage path/key."""
        raise NotImplementedError

    @abstractmethod
    async def get_raw(self, path: str) -> dict:
        """Read back a raw capture previously written by save_raw."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete a stored object; return True if it existed. Never raises."""
        raise NotImplementedError


class LocalStorageService(BaseStorageService):
    """Stores captures on the local filesystem (a Docker volume in deployment).

    Directories are created on demand. Blocking file I/O runs in a thread so it
    doesn't stall the event loop.
    """

    def __init__(self, storage_dir: str = None):
        self.storage_dir = Path(
            storage_dir or os.getenv("SCRAPE_STORAGE_DIR", DEFAULT_STORAGE_DIR)
        )

    def _run_dir(self, project_id) -> Path:
        # Partition by project then by capture date for cheap browsing/cleanup.
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.storage_dir / str(project_id) / day

    def _write_json(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def _write_bytes(self, path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)

    def _read_json(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def save_raw(self, project_id, run_id, data: dict) -> str:
        path = self._run_dir(project_id) / f"{run_id}.json"
        await asyncio.to_thread(self._write_json, path, data)
        return str(path)

    async def save_screenshot(self, project_id, run_id, image_bytes: bytes) -> str:
        path = self._run_dir(project_id) / f"{run_id}.png"
        await asyncio.to_thread(self._write_bytes, path, image_bytes)
        return str(path)

    async def get_raw(self, path: str) -> dict:
        return await asyncio.to_thread(self._read_json, Path(path))

    def _delete(self, path: Path) -> bool:
        try:
            path.unlink()
            return True
        except FileNotFoundError:
            return False
        except OSError:
            return False

    async def delete(self, path: str) -> bool:
        if not path:
            return False
        return await asyncio.to_thread(self._delete, Path(path))
