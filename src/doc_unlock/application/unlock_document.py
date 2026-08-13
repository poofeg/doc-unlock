"""Use case: unlock a document by removing its edit protection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from doc_unlock.domain.models import DocumentFormat

if TYPE_CHECKING:
    from pathlib import Path

    from doc_unlock.domain.ports import Decryptor, DocumentRepository, FileStorage
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
        repository: DocumentRepository,
        protection_service: ProtectionRemovalService,
    ) -> None:
        self._file_storage = file_storage
        self._decryptor = decryptor
        self._repository = repository
        self._protection_service = protection_service

    def execute(self, command: UnlockDocumentCommand) -> UnlockDocumentResult:
        format = DocumentFormat.from_path(command.input_path)

        data = self._file_storage.read(command.input_path)
        if command.encrypted:
            data = self._decryptor.decrypt(data, command.password)

        document = self._repository.parse(data, format)
        document = self._protection_service.remove(document)

        output = self._repository.serialize(document)
        self._file_storage.write(command.output_path, output)

        return UnlockDocumentResult(output_path=command.output_path)
