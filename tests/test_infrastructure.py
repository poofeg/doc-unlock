"""Tests for infrastructure adapters."""

import io
import zipfile

import pytest

from doc_unlock.domain.exceptions import InvalidDocumentError, InvalidPasswordError
from doc_unlock.infrastructure.ooxml import MsoffcryptoDecryptor, ZipPackageTransformer


def _unpack(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {info.filename: archive.read(info.filename) for info in archive.infolist() if not info.is_dir()}


def _strip(content: bytes) -> bytes:
    return content.replace(b'<p:modifyVerifier/>', b'').replace(b'<p:documentProtection/>', b'')


def test_transformer_streams_package_and_strips_target_part():
    transformer = ZipPackageTransformer()

    source = io.BytesIO()
    with zipfile.ZipFile(source, 'w') as archive:
        archive.writestr('[Content_Types].xml', b'<Types/>')
        archive.writestr(
            'ppt/presentation.xml',
            b'<p:presentation><p:modifyVerifier/><p:documentProtection/></p:presentation>',
        )
        archive.writestr('ppt/media/image1.png', b'x' * 1000)

    destination = io.BytesIO()
    transformer.transform(
        source,
        destination,
        target_part='ppt/presentation.xml',
        transform_part=_strip,
    )

    parts = _unpack(destination.getvalue())
    assert b'modifyVerifier' not in parts['ppt/presentation.xml']
    assert b'documentProtection' not in parts['ppt/presentation.xml']
    assert parts['[Content_Types].xml'] == b'<Types/>'
    assert parts['ppt/media/image1.png'] == b'x' * 1000


def test_decryptor_decrypts_encrypted_document(only_encrypted_pptx, encryption_password):
    decryptor = MsoffcryptoDecryptor()
    source = io.BytesIO(only_encrypted_pptx.read_bytes())
    destination = io.BytesIO()

    decryptor.decrypt(source, destination, encryption_password)

    assert 'ppt/presentation.xml' in _unpack(destination.getvalue())


def test_decryptor_wrong_password_raises(only_encrypted_pptx):
    decryptor = MsoffcryptoDecryptor()

    with pytest.raises(InvalidPasswordError):
        decryptor.decrypt(io.BytesIO(only_encrypted_pptx.read_bytes()), io.BytesIO(), 'wrong-password')


def test_decryptor_rejects_plain_document(plain_pptx, encryption_password):
    decryptor = MsoffcryptoDecryptor()

    with pytest.raises(InvalidDocumentError):
        decryptor.decrypt(io.BytesIO(plain_pptx.read_bytes()), io.BytesIO(), encryption_password)


def test_decryptor_is_encrypted(only_encrypted_pptx, plain_pptx):
    decryptor = MsoffcryptoDecryptor()

    assert decryptor.is_encrypted(io.BytesIO(only_encrypted_pptx.read_bytes())) is True
    assert decryptor.is_encrypted(io.BytesIO(plain_pptx.read_bytes())) is False


def test_transformer_rejects_non_zip():
    transformer = ZipPackageTransformer()

    with pytest.raises(InvalidDocumentError):
        transformer.transform(
            io.BytesIO(b'not a zip archive'),
            io.BytesIO(),
            target_part='ppt/presentation.xml',
            transform_part=lambda content: content,
        )
