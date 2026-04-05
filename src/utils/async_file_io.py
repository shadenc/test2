"""Non-blocking file I/O helpers for async code (Sonar: avoid sync open() in async def)."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any


async def read_text(path: Path, encoding: str = "utf-8") -> str:
    return await asyncio.to_thread(path.read_text, encoding)


async def write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    def _write() -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding=encoding)

    await asyncio.to_thread(_write)


async def read_json(path: Path) -> Any:
    raw = await read_text(path)
    return json.loads(raw)


async def write_json(path: Path, obj: Any) -> None:
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    await write_text(path, text)


async def write_bytes(path: Path, data: bytes) -> None:
    def _write() -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    await asyncio.to_thread(_write)
