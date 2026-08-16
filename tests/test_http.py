"""End-to-end tests for the FastAPI HTTP interface."""

import io
import zipfile

from fastapi.testclient import TestClient

from doc_unlock.interface.http import app

client = TestClient(app)

PPTX_MEDIA_TYPE = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'


def _unpack(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {info.filename: archive.read(info.filename) for info in archive.infolist() if not info.is_dir()}


def test_unlock_locked_file(only_locked_pptx):
    with only_locked_pptx.open('rb') as f:
        response = client.post('/unlock', files={'file': ('deck.pptx', f, PPTX_MEDIA_TYPE)})

    assert response.status_code == 200
    parts = _unpack(response.content)
    assert b'modifyVerifier' not in parts['ppt/presentation.xml']
    assert b'documentProtection' not in parts['ppt/presentation.xml']


def test_unlock_returns_attachment(only_locked_pptx):
    with only_locked_pptx.open('rb') as f:
        response = client.post('/unlock', files={'file': ('deck.pptx', f, PPTX_MEDIA_TYPE)})

    assert response.status_code == 200
    disposition = response.headers.get('content-disposition', '')
    assert 'attachment' in disposition
    assert 'unprotected' in disposition


def test_unlock_encrypted_file(encrypted_and_locked_pptx, encryption_password):
    with encrypted_and_locked_pptx.open('rb') as f:
        response = client.post(
            '/unlock',
            files={'file': ('deck.pptx', f, PPTX_MEDIA_TYPE)},
            data={'password': encryption_password},
        )

    assert response.status_code == 200
    parts = _unpack(response.content)
    assert b'modifyVerifier' not in parts['ppt/presentation.xml']
    assert b'documentProtection' not in parts['ppt/presentation.xml']


def test_unlock_wrong_password_returns_400(only_encrypted_pptx):
    with only_encrypted_pptx.open('rb') as f:
        response = client.post(
            '/unlock',
            files={'file': ('deck.pptx', f, PPTX_MEDIA_TYPE)},
            data={'password': 'wrong-password'},
        )

    assert response.status_code == 400


def test_unlock_unsupported_format_returns_415():
    response = client.post(
        '/unlock',
        files={
            'file': (
                'letter.docx',
                io.BytesIO(b'not a real docx'),
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            )
        },
    )

    assert response.status_code == 415


def test_unlock_plain_file_with_password_returns_422(plain_pptx, encryption_password):
    with plain_pptx.open('rb') as f:
        response = client.post(
            '/unlock',
            files={'file': ('deck.pptx', f, PPTX_MEDIA_TYPE)},
            data={'password': encryption_password},
        )

    assert response.status_code == 422


def test_index_serves_upload_form():
    response = client.get('/')

    assert response.status_code == 200
    assert 'action="/unlock"' in response.text
    assert 'name="file"' in response.text
