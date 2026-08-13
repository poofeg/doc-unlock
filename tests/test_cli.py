"""End-to-end tests for the Typer CLI."""

import io
import zipfile

from typer.testing import CliRunner

from doc_unlock.interface.cli import app

runner = CliRunner()


def _unpack(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {info.filename: archive.read(info.filename) for info in archive.infolist() if not info.is_dir()}


def test_unlock_command_locked_file(only_locked_pptx, tmp_path):
    output = tmp_path / 'out.pptx'

    result = runner.invoke(app, ['unlock', str(only_locked_pptx), '--no-encrypted', '-o', str(output)])

    assert result.exit_code == 0
    assert output.exists()

    parts = _unpack(output.read_bytes())
    assert b'modifyVerifier' not in parts['ppt/presentation.xml']
    assert b'documentProtection' not in parts['ppt/presentation.xml']


def test_unlock_command_encrypted_file(encrypted_and_locked_pptx, encryption_password, tmp_path):
    output = tmp_path / 'out.pptx'

    result = runner.invoke(
        app,
        ['unlock', str(encrypted_and_locked_pptx), '--password', encryption_password, '-o', str(output)],
    )

    assert result.exit_code == 0
    assert output.exists()

    parts = _unpack(output.read_bytes())
    assert b'modifyVerifier' not in parts['ppt/presentation.xml']
    assert b'documentProtection' not in parts['ppt/presentation.xml']


def test_unlock_command_default_output_name(only_locked_pptx, tmp_path):
    source = tmp_path / 'deck.pptx'
    source.write_bytes(only_locked_pptx.read_bytes())

    result = runner.invoke(app, ['unlock', str(source), '--no-encrypted'])

    assert result.exit_code == 0
    assert (tmp_path / 'deck (unprotected).pptx').exists()


def test_unlock_command_wrong_password(only_encrypted_pptx, tmp_path):
    output = tmp_path / 'out.pptx'

    result = runner.invoke(
        app,
        ['unlock', str(only_encrypted_pptx), '--password', 'wrong-password', '-o', str(output)],
    )

    assert result.exit_code == 1
    assert not output.exists()
