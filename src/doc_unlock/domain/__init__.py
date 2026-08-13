"""Domain layer: models, services, ports, and exceptions."""

from .exceptions import (
    DocumentUnlockError,
    InvalidDocumentError,
    InvalidPasswordError,
    UnsupportedFormatError,
)
from .models import Document, DocumentFormat, EditProtection, PackagePart
from .ports import Decryptor, DocumentRepository, FileStorage
from .services import ProtectionRemovalService

__all__ = [
    'Decryptor',
    'Document',
    'DocumentFormat',
    'DocumentRepository',
    'DocumentUnlockError',
    'EditProtection',
    'FileStorage',
    'InvalidDocumentError',
    'InvalidPasswordError',
    'PackagePart',
    'ProtectionRemovalService',
    'UnsupportedFormatError',
]
