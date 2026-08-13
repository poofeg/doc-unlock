"""msoffcrypto-tool implementation of the :class:`Decryptor` port."""

import io
from typing import override

import msoffcrypto

from doc_unlock.domain.exceptions import InvalidDocumentError, InvalidPasswordError
from doc_unlock.domain.ports import Decryptor


class MsoffcryptoDecryptor(Decryptor):
    @override
    def decrypt(self, data: bytes, password: str) -> bytes:
        try:
            office_file = msoffcrypto.OfficeFile(io.BytesIO(data))
        except (msoffcrypto.exceptions.FileFormatError, msoffcrypto.exceptions.ParseError) as exc:
            raise InvalidDocumentError() from exc

        if not office_file.is_encrypted():
            raise InvalidDocumentError()

        try:
            office_file.load_key(password=password)
            output = io.BytesIO()
            office_file.decrypt(output)
            return output.getvalue()
        except (msoffcrypto.exceptions.InvalidKeyError, msoffcrypto.exceptions.DecryptionError) as exc:
            raise InvalidPasswordError() from exc
