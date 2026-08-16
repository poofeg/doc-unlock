"""FastAPI HTTP interface (primary adapter)."""

import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from doc_unlock.application.dto import UnlockDocumentCommand
from doc_unlock.application.unlock_document import UnlockDocumentUseCase
from doc_unlock.domain.exceptions import (
    DocumentUnlockError,
    InvalidDocumentError,
    InvalidPasswordError,
    UnsupportedFormatError,
)
from doc_unlock.domain.services import ProtectionRemovalService
from doc_unlock.infrastructure.ooxml import MsoffcryptoDecryptor, ZipPackageTransformer

app = FastAPI(title='doc-unlock', version='0.1.0')

_MEDIA_TYPES = {
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'ppsx': 'application/vnd.openxmlformats-officedocument.presentationml.slideshow',
    'pptm': 'application/vnd.ms-powerpoint.presentation.macroEnabled.12',
    'ppsm': 'application/vnd.ms-powerpoint.slideshow.macroEnabled.12',
}

_ERROR_STATUS: dict[type[DocumentUnlockError], int] = {
    InvalidPasswordError: 400,
    UnsupportedFormatError: 415,
    InvalidDocumentError: 422,
}

_INDEX_PATH = Path(__file__).parent / 'index.html'


def _build_use_case() -> UnlockDocumentUseCase:
    return UnlockDocumentUseCase(
        decryptor=MsoffcryptoDecryptor(),
        transformer=ZipPackageTransformer(),
        protection_service=ProtectionRemovalService(),
    )


def _media_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower().lstrip('.')
    return _MEDIA_TYPES.get(suffix, 'application/octet-stream')


def _unprotected_filename(filename: str) -> str:
    path = Path(Path(filename).name)
    return f'{path.stem} (unprotected){path.suffix}'


def _to_http_error(exc: DocumentUnlockError) -> HTTPException:
    return HTTPException(status_code=_ERROR_STATUS.get(type(exc), 400), detail=str(exc))


@app.get('/')
def index() -> FileResponse:
    """Serve the minimal upload form."""
    return FileResponse(_INDEX_PATH, media_type='text/html')


@app.post('/unlock')
def unlock(
    file: Annotated[UploadFile, File(...)],
    password: Annotated[str | None, Form()] = None,
) -> FileResponse:
    """Remove edit protection from an uploaded Office document."""
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail='Upload must include a filename')

    file.file.seek(0)
    output = tempfile.NamedTemporaryFile(delete=False)
    command = UnlockDocumentCommand(
        source=file.file,
        destination=lambda: output,
        filename=filename,
        password=password,
    )

    try:
        _build_use_case().execute(command)
    except DocumentUnlockError as exc:
        output.close()
        Path(output.name).unlink(missing_ok=True)
        raise _to_http_error(exc) from exc
    except Exception:
        output.close()
        Path(output.name).unlink(missing_ok=True)
        raise

    output.close()
    return FileResponse(
        output.name,
        media_type=_media_type(filename),
        filename=_unprotected_filename(filename),
        background=BackgroundTask(Path(output.name).unlink, missing_ok=True),
    )
