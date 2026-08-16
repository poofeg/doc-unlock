"""Application-layer tests: run the use case against real fixtures."""

import io
import zipfile

import pytest

from doc_unlock.application.dto import UnlockDocumentCommand
from doc_unlock.domain.exceptions import PasswordRequiredError


def _unpack(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {info.filename: archive.read(info.filename) for info in archive.infolist() if not info.is_dir()}


def _execute(use_case, input_path, *, password=None) -> bytes:
    destination = io.BytesIO()
    with input_path.open('rb') as source:
        command = UnlockDocumentCommand(
            source=source,
            destination=lambda: destination,
            filename=input_path.name,
            password=password,
        )
        use_case.execute(command)
    return destination.getvalue()


def test_unlock_only_locked_removes_protection(use_case, only_locked_pptx):
    output = _execute(use_case, only_locked_pptx)

    input_parts = _unpack(only_locked_pptx.read_bytes())
    output_parts = _unpack(output)

    assert set(output_parts) == set(input_parts)
    assert b'modifyVerifier' not in output_parts['ppt/presentation.xml']
    assert b'documentProtection' not in output_parts['ppt/presentation.xml']

    for name, content in input_parts.items():
        if name != 'ppt/presentation.xml':
            assert output_parts[name] == content


def test_unlock_encrypted_and_locked(use_case, encrypted_and_locked_pptx, encryption_password):
    output = _execute(use_case, encrypted_and_locked_pptx, password=encryption_password)

    output_parts = _unpack(output)

    assert 'ppt/presentation.xml' in output_parts
    assert b'modifyVerifier' not in output_parts['ppt/presentation.xml']
    assert b'documentProtection' not in output_parts['ppt/presentation.xml']


def test_unlock_only_encrypted_decrypts(use_case, only_encrypted_pptx, encryption_password):
    output = _execute(use_case, only_encrypted_pptx, password=encryption_password)

    output_parts = _unpack(output)

    assert 'ppt/presentation.xml' in output_parts
    assert b'modifyVerifier' not in output_parts['ppt/presentation.xml']
    assert b'documentProtection' not in output_parts['ppt/presentation.xml']


def test_unlock_plain_has_no_protection(use_case, plain_pptx):
    output = _execute(use_case, plain_pptx)

    input_parts = _unpack(plain_pptx.read_bytes())
    output_parts = _unpack(output)

    assert set(output_parts) == set(input_parts)
    assert b'modifyVerifier' not in output_parts['ppt/presentation.xml']
    assert b'documentProtection' not in output_parts['ppt/presentation.xml']


def test_unlock_plain_with_password_ignores_password(use_case, plain_pptx, encryption_password):
    output = _execute(use_case, plain_pptx, password=encryption_password)

    input_parts = _unpack(plain_pptx.read_bytes())
    output_parts = _unpack(output)

    assert set(output_parts) == set(input_parts)
    assert b'modifyVerifier' not in output_parts['ppt/presentation.xml']
    assert b'documentProtection' not in output_parts['ppt/presentation.xml']


def test_unlock_encrypted_without_password_raises(use_case, only_encrypted_pptx):
    with pytest.raises(PasswordRequiredError):
        _execute(use_case, only_encrypted_pptx)
