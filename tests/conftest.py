"""Shared fixtures for the test suite."""

from pathlib import Path

import pytest

from doc_unlock.application.unlock_document import UnlockDocumentUseCase
from doc_unlock.domain.services import ProtectionRemovalService
from doc_unlock.infrastructure.ooxml import MsoffcryptoDecryptor, ZipPackageTransformer

PPTX_DIR = Path(__file__).resolve().parent / 'fixtures' / 'pptx'
DOCX_DIR = Path(__file__).resolve().parent / 'fixtures' / 'docx'
XLSX_DIR = Path(__file__).resolve().parent / 'fixtures' / 'xlsx'


@pytest.fixture
def plain_pptx() -> Path:
    return PPTX_DIR / 'plain.pptx'


@pytest.fixture
def only_locked_pptx() -> Path:
    return PPTX_DIR / 'only-locked.pptx'


@pytest.fixture
def only_encrypted_pptx() -> Path:
    return PPTX_DIR / 'only-encrypted.pptx'


@pytest.fixture
def encrypted_and_locked_pptx() -> Path:
    return PPTX_DIR / 'encrypted-and-locked.pptx'


@pytest.fixture
def plain_docx() -> Path:
    return DOCX_DIR / 'plain.docx'


@pytest.fixture
def only_locked_docx() -> Path:
    return DOCX_DIR / 'only-locked.docx'


@pytest.fixture
def only_encrypted_docx() -> Path:
    return DOCX_DIR / 'only-encrypted.docx'


@pytest.fixture
def encrypted_and_locked_docx() -> Path:
    return DOCX_DIR / 'encrypted-and-locked.docx'


@pytest.fixture
def plain_xlsx() -> Path:
    return XLSX_DIR / 'plain.xlsx'


@pytest.fixture
def only_locked_xlsx() -> Path:
    return XLSX_DIR / 'only-locked.xlsx'


@pytest.fixture
def only_encrypted_xlsx() -> Path:
    return XLSX_DIR / 'only-encrypted.xlsx'


@pytest.fixture
def encrypted_and_locked_xlsx() -> Path:
    return XLSX_DIR / 'encrypted-and-locked.xlsx'


@pytest.fixture
def encryption_password() -> str:
    return '111'


@pytest.fixture
def use_case() -> UnlockDocumentUseCase:
    return UnlockDocumentUseCase(
        decryptor=MsoffcryptoDecryptor(),
        transformer=ZipPackageTransformer(),
        protection_service=ProtectionRemovalService(),
    )
