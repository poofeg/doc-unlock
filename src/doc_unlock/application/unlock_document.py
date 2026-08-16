"""Use case: unlock a document by removing its edit protection."""

import tempfile
from contextlib import ExitStack
from dataclasses import dataclass
from typing import TYPE_CHECKING

from doc_unlock.domain.models import DocumentFormat

if TYPE_CHECKING:
    from pathlib import Path
    from typing import IO

    from doc_unlock.domain.ports import Decryptor, FileStorage, PackageTransformer
    from doc_unlock.domain.services import ProtectionRemovalService

    from .dto import UnlockDocumentCommand


@dataclass(frozen=True)
class UnlockDocumentResult:
    output_path: Path


class UnlockDocumentUseCase:
    """Orchestrates loading, unlocking, and saving a document."""

    def __init__(
        self,
        file_storage: FileStorage,
        decryptor: Decryptor,
        transformer: PackageTransformer,
        protection_service: ProtectionRemovalService,
    ) -> None:
        self._file_storage = file_storage
        self._decryptor = decryptor
        self._transformer = transformer
        self._protection_service = protection_service

    def execute(self, command: UnlockDocumentCommand) -> UnlockDocumentResult:
        format = DocumentFormat.from_path(command.input_path)
        protection = self._protection_service.protection_for(format)

        with ExitStack() as stack:
            source: IO[bytes]
            if command.encrypted:
                source = stack.enter_context(self._file_storage.open_read(command.input_path))
                decrypted = stack.enter_context(tempfile.SpooledTemporaryFile(max_size=10 * 1024 * 1024))
                self._decryptor.decrypt(source, decrypted, command.password)
                decrypted.seek(0)
                source = decrypted
            else:
                source = stack.enter_context(self._file_storage.open_read(command.input_path))

            destination = stack.enter_context(self._file_storage.open_write(command.output_path))
            self._transformer.transform(
                source,
                destination,
                target_part=protection.part_name,
                transform_part=lambda content: self._protection_service.strip(content, protection),
            )

        return UnlockDocumentResult(output_path=command.output_path)
