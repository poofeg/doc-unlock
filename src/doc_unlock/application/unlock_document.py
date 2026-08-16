"""Use case: unlock a document by removing its edit protection."""

import tempfile
from contextlib import ExitStack
from typing import TYPE_CHECKING

from doc_unlock.domain.exceptions import PasswordRequiredError
from doc_unlock.domain.models import DocumentFormat

if TYPE_CHECKING:
    from typing import IO

    from doc_unlock.domain.ports import Decryptor, PackageTransformer
    from doc_unlock.domain.services import ProtectionRemovalService

    from .dto import UnlockDocumentCommand


class UnlockDocumentUseCase:
    """Orchestrates decryption and edit-protection removal on open streams."""

    def __init__(
        self,
        decryptor: Decryptor,
        transformer: PackageTransformer,
        protection_service: ProtectionRemovalService,
    ) -> None:
        self._decryptor = decryptor
        self._transformer = transformer
        self._protection_service = protection_service

    def execute(self, command: UnlockDocumentCommand) -> None:
        format = DocumentFormat.from_filename(command.filename)
        protection = self._protection_service.protection_for(format)

        source: IO[bytes] = command.source
        encrypted = self._decryptor.is_encrypted(source)
        source.seek(0)

        with ExitStack() as stack:
            if encrypted:
                if command.password is None:
                    raise PasswordRequiredError()
                decrypted = stack.enter_context(tempfile.SpooledTemporaryFile(max_size=10 * 1024 * 1024))
                self._decryptor.decrypt(source, decrypted, command.password)
                decrypted.seek(0)
                source = decrypted

            destination = command.destination()
            self._transformer.transform(
                source,
                destination,
                target_part=protection.part_name,
                transform_part=lambda content: self._protection_service.strip(content, protection),
            )
