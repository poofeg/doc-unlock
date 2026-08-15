"""Ports (interfaces) implemented by the infrastructure layer."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from .models import Document, DocumentFormat


class FileStorage(ABC):
    """Raw file-system access."""

    @abstractmethod
    def read(self, path: Path) -> bytes: ...

    @abstractmethod
    def write(self, path: Path, data: bytes) -> None: ...


class Decryptor(ABC):
    """Decrypts encrypted Office documents."""

    @abstractmethod
    def decrypt(self, data: bytes, password: str) -> bytes: ...


class DocumentRepository(ABC):
    """Codec between raw OOXML bytes and a :class:`Document` aggregate."""

    @abstractmethod
    def parse(self, data: bytes, format: DocumentFormat) -> Document: ...

    @abstractmethod
    def serialize(self, document: Document) -> bytes: ...
