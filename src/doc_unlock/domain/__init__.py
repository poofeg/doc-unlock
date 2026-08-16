"""Domain layer: models, services, ports, and exceptions."""

from .exceptions import (
    DocumentUnlockError,
    InvalidDocumentError,
    InvalidPasswordError,
    PasswordRequiredError,
    UnsupportedFormatError,
)
from .models import DocumentFormat, EditProtection
from .ports import Decryptor, FileStorage, PackageTransformer
from .services import ProtectionRemovalService

__all__ = [
    'Decryptor',
    'DocumentFormat',
    'DocumentUnlockError',
    'EditProtection',
    'FileStorage',
    'InvalidDocumentError',
    'InvalidPasswordError',
    'PackageTransformer',
    'PasswordRequiredError',
    'ProtectionRemovalService',
    'UnsupportedFormatError',
]
