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


class InvalidDocumentError(DocumentUnlockError):
    """Raised when the file is not a valid encrypted Office document."""

    def __init__(self) -> None:
        super().__init__('The file is not a valid encrypted Office document')
