"""Ports (interfaces) implemented by the infrastructure layer."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from typing import IO


class FileStorage(ABC):
    """Raw file-system access."""

    @abstractmethod
    def open_read(self, path: Path) -> IO[bytes]: ...

    @abstractmethod
    def open_write(self, path: Path) -> IO[bytes]: ...


class Decryptor(ABC):
    """Decrypts an encrypted Office document into a destination stream."""

    @abstractmethod
    def decrypt(self, source: IO[bytes], destination: IO[bytes], password: str) -> None: ...

    @abstractmethod
    def is_encrypted(self, source: IO[bytes]) -> bool: ...


class PackageTransformer(ABC):
    """Streams an OOXML package, transforming a single target part."""

    @abstractmethod
    def transform(
        self,
        source: IO[bytes],
        destination: IO[bytes],
        target_part: str,
        transform_part: Callable[[bytes], bytes],
    ) -> None: ...
