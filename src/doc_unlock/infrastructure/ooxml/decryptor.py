"""msoffcrypto-tool implementation of the :class:`Decryptor` port."""

from typing import TYPE_CHECKING, override

import msoffcrypto

from doc_unlock.domain.exceptions import InvalidDocumentError, InvalidPasswordError
from doc_unlock.domain.ports import Decryptor

if TYPE_CHECKING:
    from typing import IO


class MsoffcryptoDecryptor(Decryptor):
    @override
    def decrypt(self, source: IO[bytes], destination: IO[bytes], password: str) -> None:
        try:
            office_file = msoffcrypto.OfficeFile(source)
        except (msoffcrypto.exceptions.FileFormatError, msoffcrypto.exceptions.ParseError) as exc:
            raise InvalidDocumentError() from exc

        if not office_file.is_encrypted():
            raise InvalidDocumentError()

        try:
            office_file.load_key(password=password)
            office_file.decrypt(destination)
        except (msoffcrypto.exceptions.InvalidKeyError, msoffcrypto.exceptions.DecryptionError) as exc:
            raise InvalidPasswordError() from exc

    @override
    def is_encrypted(self, source: IO[bytes]) -> bool:
        try:
            office_file = msoffcrypto.OfficeFile(source)
        except msoffcrypto.exceptions.FileFormatError, msoffcrypto.exceptions.ParseError:
            return False
        result: bool = office_file.is_encrypted()
        return result
