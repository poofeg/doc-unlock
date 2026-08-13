"""Infrastructure layer: adapters implementing domain ports."""

from .filesystem import LocalFileStorage
from .ooxml import MsoffcryptoDecryptor, OoxmlDocumentRepository

__all__ = ['LocalFileStorage', 'MsoffcryptoDecryptor', 'OoxmlDocumentRepository']
