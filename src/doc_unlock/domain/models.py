"""Domain models."""

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from .exceptions import UnsupportedFormatError

if TYPE_CHECKING:
    from pathlib import Path


class DocumentFormat(StrEnum):
    """OOXML document formats known to the application."""

    PPTX = 'pptx'
    DOCX = 'docx'
    XLSX = 'xlsx'

    @classmethod
    def from_path(cls, path: Path) -> DocumentFormat:
        suffix = path.suffix.lower().lstrip('.')
        format = _SUFFIX_TO_FORMAT.get(suffix)
        if format is None:
            raise UnsupportedFormatError(suffix)
        return format


# PowerPoint keeps the same OOXML package across these extensions.
_SUFFIX_TO_FORMAT: dict[str, DocumentFormat] = {
    'pptx': DocumentFormat.PPTX,
    'ppsx': DocumentFormat.PPTX,
    'pptm': DocumentFormat.PPTX,
    'ppsm': DocumentFormat.PPTX,
    'docx': DocumentFormat.DOCX,
    'xlsx': DocumentFormat.XLSX,
}


@dataclass(frozen=True)
class EditProtection:
    """Where and how edit protection is stored inside a document package."""

    part_name: str
    namespace: str
    element_names: tuple[str, ...]
