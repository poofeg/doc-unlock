"""File-system implementation of the :class:`FileStorage` port."""

from typing import TYPE_CHECKING, override

from doc_unlock.domain.ports import FileStorage

if TYPE_CHECKING:
    from pathlib import Path


class LocalFileStorage(FileStorage):
    @override
    def read(self, path: Path) -> bytes:
        return path.read_bytes()

    @override
    def write(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
