"""Typer CLI interface (primary adapter)."""

import logging
from contextlib import ExitStack
from pathlib import Path  # noqa: TC003
from typing import Annotated, NoReturn

import typer

from doc_unlock.application.dto import UnlockDocumentCommand
from doc_unlock.application.unlock_document import UnlockDocumentUseCase
from doc_unlock.domain.exceptions import (
    DocumentUnlockError,
    InvalidPasswordError,
    UnsupportedFormatError,
)
from doc_unlock.domain.services import ProtectionRemovalService
from doc_unlock.infrastructure.filesystem import LocalFileStorage
from doc_unlock.infrastructure.ooxml import (
    MsoffcryptoDecryptor,
    ZipPackageTransformer,
)

logger = logging.getLogger(__name__)

app = typer.Typer()


def _build_use_case() -> UnlockDocumentUseCase:
    return UnlockDocumentUseCase(
        decryptor=MsoffcryptoDecryptor(),
        transformer=ZipPackageTransformer(),
        protection_service=ProtectionRemovalService(),
    )


def _default_output_path(input_path: Path) -> Path:
    return input_path.with_name(f'{input_path.stem} (unprotected){input_path.suffix}')


def _fail(message: str) -> NoReturn:
    typer.secho(f'Error: {message}', fg=typer.colors.RED, err=True)
    raise typer.Exit(code=1)


@app.callback()
def _app_callback() -> None:
    """Unlock Microsoft Office documents by removing edit protection."""


@app.command()
def unlock(
    input_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            dir_okay=False,
            readable=True,
            help='Path to the protected document.',
        ),
    ],
    password: Annotated[
        str | None,
        typer.Option(
            '--password',
            '-p',
            help='Password used to decrypt an encrypted document. Omit if the file is not encrypted.',
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            '--output',
            '-o',
            help="Where to save the unlocked document. Defaults to '<name> (unprotected).<ext>'.",
        ),
    ] = None,
) -> None:
    """Remove edit protection from a Microsoft Office document."""
    output_path = output or _default_output_path(input_path)
    storage = LocalFileStorage()

    try:
        with ExitStack() as stack:
            source = stack.enter_context(storage.open_read(input_path))
            command = UnlockDocumentCommand(
                source=source,
                destination=lambda: stack.enter_context(storage.open_write(output_path)),
                filename=input_path.name,
                password=password,
            )
            _build_use_case().execute(command)
    except InvalidPasswordError as exc:
        _fail(str(exc))
    except UnsupportedFormatError as exc:
        _fail(str(exc))
    except DocumentUnlockError as exc:
        _fail(str(exc))
    except Exception:
        logger.exception('Unexpected error while unlocking document')
        _fail('Unexpected error. See logs for details.')

    typer.secho(f'Protection removed: {output_path}', fg=typer.colors.GREEN)
