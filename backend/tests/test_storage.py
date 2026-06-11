"""LocalStorageService round-trip, directory creation, path format."""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.services.storage import LocalStorageService


async def test_local_storage_save_and_retrieve(tmp_path):
    storage = LocalStorageService(storage_dir=str(tmp_path))
    project_id, run_id = uuid.uuid4(), uuid.uuid4()
    data = {"answer_text": "hello", "sources": ["https://a.test"]}
    path = await storage.save_raw(project_id, run_id, data)
    assert await storage.get_raw(path) == data


async def test_storage_creates_directories(tmp_path):
    storage = LocalStorageService(storage_dir=str(tmp_path))
    project_id, run_id = uuid.uuid4(), uuid.uuid4()
    path = await storage.save_raw(project_id, run_id, {"k": "v"})
    assert Path(path).exists()
    assert Path(path).parent.is_dir()


async def test_storage_path_format(tmp_path):
    storage = LocalStorageService(storage_dir=str(tmp_path))
    project_id, run_id = uuid.uuid4(), uuid.uuid4()
    path = await storage.save_raw(project_id, run_id, {"k": "v"})
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert str(project_id) in path
    assert today in path
    assert path.endswith(f"{run_id}.json")
