"""Tests for infrastructure adapters."""

import io
import zipfile

import pytest

from doc_unlock.domain.exceptions import InvalidDocumentError, InvalidPasswordError
from doc_unlock.domain.models import DocumentFormat
from doc_unlock.infrastructure.ooxml import MsoffcryptoDecryptor, OoxmlDocumentRepository


def _unpack(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {info.filename: archive.read(info.filename) for info in archive.infolist() if not info.is_dir()}


def test_repository_parse_serialize_round_trip():
    repository = OoxmlDocumentRepository()

    source = io.BytesIO()
    with zipfile.ZipFile(source, 'w') as archive:
        archive.writestr('[Content_Types].xml', b'<Types/>')
        archive.writestr('ppt/presentation.xml', b'<p:presentation/>')

    document = repository.parse(source.getvalue(), DocumentFormat.PPTX)
    serialized = repository.serialize(document)

    assert _unpack(serialized) == {
        '[Content_Types].xml': b'<Types/>',
        'ppt/presentation.xml': b'<p:presentation/>',
    }


def test_decryptor_decrypts_encrypted_document(only_encrypted_pptx, encryption_password):
    decryptor = MsoffcryptoDecryptor()

    decrypted = decryptor.decrypt(only_encrypted_pptx.read_bytes(), encryption_password)

    assert 'ppt/presentation.xml' in _unpack(decrypted)


def test_decryptor_wrong_password_raises(only_encrypted_pptx):
    decryptor = MsoffcryptoDecryptor()

    with pytest.raises(InvalidPasswordError):
        decryptor.decrypt(only_encrypted_pptx.read_bytes(), 'wrong-password')


def test_decryptor_rejects_plain_document(plain_pptx, encryption_password):
    decryptor = MsoffcryptoDecryptor()

    with pytest.raises(InvalidDocumentError):
        decryptor.decrypt(plain_pptx.read_bytes(), encryption_password)
