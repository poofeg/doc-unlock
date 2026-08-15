"""Unit tests for the domain layer."""

from pathlib import Path

import pytest

from doc_unlock.domain.exceptions import UnsupportedFormatError
from doc_unlock.domain.models import DocumentFormat, EditProtection
from doc_unlock.domain.services import ProtectionRemovalService

PRESENTATION_NS = 'http://schemas.openxmlformats.org/presentationml/2006/main'

PROTECTION = EditProtection(
    part_name='ppt/presentation.xml',
    namespace=PRESENTATION_NS,
    element_names=('modifyVerifier', 'documentProtection'),
)


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


def test_protection_for_returns_pptx_protection():
    protection = ProtectionRemovalService.protection_for(DocumentFormat.PPTX)

    assert protection.part_name == 'ppt/presentation.xml'
    assert protection.element_names == ('modifyVerifier', 'documentProtection')


def test_protection_for_unsupported_format_raises():
    with pytest.raises(UnsupportedFormatError):
        ProtectionRemovalService.protection_for(DocumentFormat.DOCX)


def test_strip_removes_protection_elements():
    stripped = ProtectionRemovalService.strip(_presentation_with_protection(), PROTECTION)

    assert b'modifyVerifier' not in stripped
    assert b'documentProtection' not in stripped
    assert b'sldMasterIdLst' in stripped
    assert b'notesMasterIdLst' in stripped
