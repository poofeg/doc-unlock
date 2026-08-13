"""Application-layer tests: run the use case against real fixtures."""

import io
import zipfile

from doc_unlock.application.dto import UnlockDocumentCommand


def _unpack(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {info.filename: archive.read(info.filename) for info in archive.infolist() if not info.is_dir()}


def _execute(use_case, input_path, output_path, *, encrypted, password=''):
    return use_case.execute(
        UnlockDocumentCommand(
            input_path=input_path,
            output_path=output_path,
            password=password,
            encrypted=encrypted,
        )
    )


def test_unlock_only_locked_removes_protection(use_case, only_locked_pptx, tmp_path):
    output = tmp_path / 'out.pptx'
    _execute(use_case, only_locked_pptx, output, encrypted=False)

    input_parts = _unpack(only_locked_pptx.read_bytes())
    output_parts = _unpack(output.read_bytes())

    assert set(output_parts) == set(input_parts)
    assert b'modifyVerifier' not in output_parts['ppt/presentation.xml']
    assert b'documentProtection' not in output_parts['ppt/presentation.xml']

    for name, content in input_parts.items():
        if name != 'ppt/presentation.xml':
            assert output_parts[name] == content


def test_unlock_encrypted_and_locked(use_case, encrypted_and_locked_pptx, encryption_password, tmp_path):
    output = tmp_path / 'out.pptx'
    _execute(use_case, encrypted_and_locked_pptx, output, encrypted=True, password=encryption_password)

    output_parts = _unpack(output.read_bytes())

    assert 'ppt/presentation.xml' in output_parts
    assert b'modifyVerifier' not in output_parts['ppt/presentation.xml']
    assert b'documentProtection' not in output_parts['ppt/presentation.xml']


def test_unlock_only_encrypted_decrypts(use_case, only_encrypted_pptx, encryption_password, tmp_path):
    output = tmp_path / 'out.pptx'
    _execute(use_case, only_encrypted_pptx, output, encrypted=True, password=encryption_password)

    output_parts = _unpack(output.read_bytes())

    assert 'ppt/presentation.xml' in output_parts
    assert b'modifyVerifier' not in output_parts['ppt/presentation.xml']
    assert b'documentProtection' not in output_parts['ppt/presentation.xml']


def test_unlock_plain_has_no_protection(use_case, plain_pptx, tmp_path):
    output = tmp_path / 'out.pptx'
    _execute(use_case, plain_pptx, output, encrypted=False)

    input_parts = _unpack(plain_pptx.read_bytes())
    output_parts = _unpack(output.read_bytes())

    assert set(output_parts) == set(input_parts)
    assert b'modifyVerifier' not in output_parts['ppt/presentation.xml']
    assert b'documentProtection' not in output_parts['ppt/presentation.xml']
