"""Domain models."""

from __future__ import annotations

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
class PackagePart:
    """A single part (file) inside an OOXML package."""

    name: str
    content: bytes


@dataclass(frozen=True)
class EditProtection:
    """Where and how edit protection is stored inside a document package."""

    part_name: str
    namespace: str
    element_names: tuple[str, ...]


@dataclass
class Document:
    """A document aggregate: an OOXML package and its parts."""

    format: DocumentFormat
    parts: list[PackagePart]

    def get_part(self, name: str) -> PackagePart | None:
        for part in self.parts:
            if part.name == name:
                return part
        return None
