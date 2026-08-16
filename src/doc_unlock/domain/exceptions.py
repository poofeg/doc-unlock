"""Domain exceptions."""


class DocumentUnlockError(Exception):
    """Base class for all errors in the document-unlocking domain."""


class UnsupportedFormatError(DocumentUnlockError):
    """Raised when a document format is not supported."""

    def __init__(self, suffix: str | None = None) -> None:
        self.suffix = suffix
        message = f'Unsupported document format: {suffix}' if suffix else 'Unsupported document format'
        super().__init__(message)


class InvalidPasswordError(DocumentUnlockError):
    """Raised when the provided password cannot decrypt the document."""

    def __init__(self) -> None:
        super().__init__('Invalid password or unsupported encryption')


class PasswordRequiredError(DocumentUnlockError):
    """Raised when the document is encrypted and no password was provided."""

    def __init__(self) -> None:
        super().__init__('This document is encrypted and requires a password')


class InvalidDocumentError(DocumentUnlockError):
    """Raised when the file is not a valid Office document."""

    def __init__(self, message: str = 'The file is not a valid Office document') -> None:
        super().__init__(message)
