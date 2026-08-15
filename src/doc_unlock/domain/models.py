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
        try:
            return cls(suffix)
        except ValueError as exc:
            raise UnsupportedFormatError(suffix) from exc


@dataclass(frozen=True)
class EditProtection:
    """Where and how edit protection is stored inside a document package."""

    part_name: str
    namespace: str
    element_names: tuple[str, ...]
