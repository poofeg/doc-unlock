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
    element_names=('modifyVerifier',),
)


def _presentation_with_protection() -> bytes:
    return (
        '<?xml version="1.0"?>'
        f'<p:presentation xmlns:p="{PRESENTATION_NS}">'
        '<p:sldMasterIdLst/>'
        '<p:modifyVerifier cryptProviderType="rsaAES"/>'
        '<p:notesMasterIdLst/>'
        '</p:presentation>'
    ).encode()


def test_from_path_maps_known_suffixes():
    assert DocumentFormat.from_path(Path('deck.pptx')) is DocumentFormat.PPTX
    assert DocumentFormat.from_path(Path('letter.docx')) is DocumentFormat.DOCX
    assert DocumentFormat.from_path(Path('book.xlsx')) is DocumentFormat.XLSX


def test_from_path_maps_powerpoint_variants():
    assert DocumentFormat.from_path(Path('deck.ppsx')) is DocumentFormat.PPTX
    assert DocumentFormat.from_path(Path('deck.pptm')) is DocumentFormat.PPTX
    assert DocumentFormat.from_path(Path('deck.ppsm')) is DocumentFormat.PPTX


def test_from_path_is_case_insensitive():
    assert DocumentFormat.from_path(Path('DECK.PPTX')) is DocumentFormat.PPTX


def test_from_path_unknown_suffix_raises():
    with pytest.raises(UnsupportedFormatError):
        DocumentFormat.from_path(Path('archive.zip'))


def test_from_path_without_suffix_raises():
    with pytest.raises(UnsupportedFormatError):
        DocumentFormat.from_path(Path('no_suffix'))


def test_from_filename_maps_known_suffixes():
    assert DocumentFormat.from_filename('deck.pptx') is DocumentFormat.PPTX
    assert DocumentFormat.from_filename('letter.docx') is DocumentFormat.DOCX
    assert DocumentFormat.from_filename('book.xlsx') is DocumentFormat.XLSX


def test_from_filename_maps_powerpoint_variants():
    assert DocumentFormat.from_filename('deck.ppsx') is DocumentFormat.PPTX
    assert DocumentFormat.from_filename('deck.pptm') is DocumentFormat.PPTX
    assert DocumentFormat.from_filename('deck.ppsm') is DocumentFormat.PPTX


def test_from_filename_is_case_insensitive():
    assert DocumentFormat.from_filename('DECK.PPTX') is DocumentFormat.PPTX


def test_from_filename_unknown_suffix_raises():
    with pytest.raises(UnsupportedFormatError):
        DocumentFormat.from_filename('archive.zip')


def test_from_filename_without_suffix_raises():
    with pytest.raises(UnsupportedFormatError):
        DocumentFormat.from_filename('no_suffix')


def test_protection_for_returns_pptx_protection():
    protection = ProtectionRemovalService.protection_for(DocumentFormat.PPTX)

    assert protection.part_name == 'ppt/presentation.xml'
    assert protection.element_names == ('modifyVerifier',)


def test_protection_for_returns_docx_protection():
    protection = ProtectionRemovalService.protection_for(DocumentFormat.DOCX)

    assert protection.part_name == 'word/settings.xml'
    assert protection.element_names == ('writeProtection', 'documentProtection')


def test_protection_for_returns_xlsx_protection():
    protection = ProtectionRemovalService.protection_for(DocumentFormat.XLSX)

    assert protection.part_name == 'xl/workbook.xml'
    assert protection.element_names == ('fileSharing', 'workbookProtection')


def test_strip_removes_protection_elements():
    stripped = ProtectionRemovalService.strip(_presentation_with_protection(), PROTECTION)

    assert b'modifyVerifier' not in stripped
    assert b'sldMasterIdLst' in stripped
    assert b'notesMasterIdLst' in stripped


def test_strip_preserves_namespace_prefixes():
    content = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<w:settings xmlns:w="http://word" xmlns:mc="http://mc" mc:Ignorable="w14">'
        b'<w:writeProtection/>'
        b'<w:zoom/>'
        b'</w:settings>'
    )
    protection = EditProtection(
        part_name='word/settings.xml',
        namespace='http://word',
        element_names=('writeProtection',),
    )

    stripped = ProtectionRemovalService.strip(content, protection)

    assert b'xmlns:w="http://word"' in stripped
    assert b'mc:Ignorable="w14"' in stripped
    assert b'ns0' not in stripped
    assert b'writeProtection' not in stripped


def test_strip_preserves_unused_namespace_declarations():
    # DOCX settings.xml declares prefixes (e.g. r, w14) referenced only by
    # mc:Ignorable. ElementTree drops those unused declarations and corrupts the
    # file; lxml must keep them.
    content = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<w:settings xmlns:w="http://word" xmlns:r="http://relationships" '
        b'xmlns:mc="http://mc" mc:Ignorable="w14 r">'
        b'<w:writeProtection/>'
        b'<w:zoom/>'
        b'</w:settings>'
    )
    protection = EditProtection(
        part_name='word/settings.xml',
        namespace='http://word',
        element_names=('writeProtection',),
    )

    stripped = ProtectionRemovalService.strip(content, protection)

    assert b'xmlns:r="http://relationships"' in stripped
    assert b'mc:Ignorable="w14 r"' in stripped
    assert b'writeProtection' not in stripped
