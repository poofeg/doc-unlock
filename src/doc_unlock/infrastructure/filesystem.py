"""File-system implementation of the :class:`FileStorage` port."""

from typing import TYPE_CHECKING, override

from doc_unlock.domain.ports import FileStorage

if TYPE_CHECKING:
    from pathlib import Path
    from typing import BinaryIO


class LocalFileStorage(FileStorage):
    @override
    def open_read(self, path: Path) -> BinaryIO:
        return path.open('rb')

    @override
    def open_write(self, path: Path) -> BinaryIO:
        path.parent.mkdir(parents=True, exist_ok=True)
        return path.open('wb')
