"""Unit tests for the domain layer."""

from pathlib import Path

import pytest

from doc_unlock.domain.exceptions import UnsupportedFormatError
from doc_unlock.domain.models import Document, DocumentFormat, PackagePart
from doc_unlock.domain.services import ProtectionRemovalService

PRESENTATION_NS = 'http://schemas.openxmlformats.org/presentationml/2006/main'


def _presentation_with_protection() -> bytes:
    return (
        '<?xml version="1.0"?>'
        f'<p:presentation xmlns:p="{PRESENTATION_NS}">'
        '<p:sldMasterIdLst/>'
        '<p:modifyVerifier cryptProviderType="rsaAES"/>'
        '<p:documentProtection/>'
        '<p:notesMasterIdLst/>'
        '</p:presentation>'
    ).encode()


def test_from_path_maps_known_suffixes():
    assert DocumentFormat.from_path(Path('deck.pptx')) is DocumentFormat.PPTX
    assert DocumentFormat.from_path(Path('letter.docx')) is DocumentFormat.DOCX
    assert DocumentFormat.from_path(Path('book.xlsx')) is DocumentFormat.XLSX


def test_from_path_is_case_insensitive():
    assert DocumentFormat.from_path(Path('DECK.PPTX')) is DocumentFormat.PPTX


def test_from_path_unknown_suffix_raises():
    with pytest.raises(UnsupportedFormatError):
        DocumentFormat.from_path(Path('archive.zip'))


def test_from_path_without_suffix_raises():
    with pytest.raises(UnsupportedFormatError):
        DocumentFormat.from_path(Path('no_suffix'))


def test_remove_strips_protection_elements():
    service = ProtectionRemovalService()
    document = Document(
        format=DocumentFormat.PPTX,
        parts=[
            PackagePart(name='[Content_Types].xml', content=b'<Types/>'),
            PackagePart(name='ppt/presentation.xml', content=_presentation_with_protection()),
        ],
    )

    result = service.remove(document)

    presentation = result.get_part('ppt/presentation.xml')
    assert presentation is not None
    assert b'modifyVerifier' not in presentation.content
    assert b'documentProtection' not in presentation.content
    assert b'sldMasterIdLst' in presentation.content
    assert b'notesMasterIdLst' in presentation.content

    content_types = result.get_part('[Content_Types].xml')
    assert content_types is not None
    assert content_types.content == b'<Types/>'


def test_remove_without_protection_part_keeps_parts():
    service = ProtectionRemovalService()
    document = Document(
        format=DocumentFormat.PPTX,
        parts=[PackagePart(name='[Content_Types].xml', content=b'<Types/>')],
    )

    result = service.remove(document)

    assert len(result.parts) == 1
    assert result.parts[0].name == '[Content_Types].xml'
    assert result.parts[0].content == b'<Types/>'


def test_remove_unsupported_format_raises():
    service = ProtectionRemovalService()
    document = Document(format=DocumentFormat.DOCX, parts=[])

    with pytest.raises(UnsupportedFormatError):
        service.remove(document)
