"""Shared fixtures for the test suite."""

from pathlib import Path

import pytest

from doc_unlock.application.unlock_document import UnlockDocumentUseCase
from doc_unlock.domain.services import ProtectionRemovalService
from doc_unlock.infrastructure.filesystem import LocalFileStorage
from doc_unlock.infrastructure.ooxml import MsoffcryptoDecryptor, ZipPackageTransformer

PPTX_DIR = Path(__file__).resolve().parent / 'fixtures' / 'pptx'


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
def encryption_password() -> str:
    return '111'


@pytest.fixture
def use_case() -> UnlockDocumentUseCase:
    return UnlockDocumentUseCase(
        file_storage=LocalFileStorage(),
        decryptor=MsoffcryptoDecryptor(),
        transformer=ZipPackageTransformer(),
        protection_service=ProtectionRemovalService(),
    )
