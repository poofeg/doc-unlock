"""OOXML infrastructure: decryptor and repository."""

from .decryptor import MsoffcryptoDecryptor
from .repository import OoxmlDocumentRepository

__all__ = ['MsoffcryptoDecryptor', 'OoxmlDocumentRepository']
