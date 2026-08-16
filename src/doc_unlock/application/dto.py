"""Application-layer data transfer objects."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import IO


@dataclass(frozen=True)
class UnlockDocumentCommand:
    """A request to unlock a document, expressed as open streams.

    ``source`` is an already-open, seekable binary stream to read from.
    ``destination`` is a zero-argument callable returning an already-open,
    seekable binary stream to write to. It is invoked lazily so the
    destination is only created after the source has been validated and,
    when a password is given, decrypted.
    """

    source: IO[bytes]
    destination: Callable[[], IO[bytes]]
    filename: str
    password: str | None
