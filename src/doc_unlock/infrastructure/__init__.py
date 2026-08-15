"""Infrastructure layer: adapters implementing domain ports."""

from .filesystem import LocalFileStorage
from .ooxml import MsoffcryptoDecryptor, ZipPackageTransformer

__all__ = ['LocalFileStorage', 'MsoffcryptoDecryptor', 'ZipPackageTransformer']
