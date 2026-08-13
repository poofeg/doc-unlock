"""OOXML implementation of the :class:`DocumentRepository` port."""

import io
import zipfile
from typing import override

from doc_unlock.domain.models import Document, DocumentFormat, PackagePart
from doc_unlock.domain.ports import DocumentRepository


class OoxmlDocumentRepository(DocumentRepository):
    @override
    def parse(self, data: bytes, format: DocumentFormat) -> Document:
        parts: list[PackagePart] = []
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                parts.append(PackagePart(name=info.filename, content=archive.read(info.filename)))
        return Document(format=format, parts=parts)

    @override
    def serialize(self, document: Document) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
            for part in document.parts:
                archive.writestr(part.name, part.content)
        return buffer.getvalue()
