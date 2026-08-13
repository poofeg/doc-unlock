"""Domain services: pure business logic."""

import xml.etree.ElementTree as ET  # noqa: S405

from .exceptions import UnsupportedFormatError
from .models import Document, DocumentFormat, EditProtection, PackagePart

# Mapping of format -> where edit protection lives and how to strip it.
# Only PPTX is implemented for now; DOCX/XLSX are recognized but not yet supported.
_PROTECTION_BY_FORMAT: dict[DocumentFormat, EditProtection] = {
    DocumentFormat.PPTX: EditProtection(
        part_name='ppt/presentation.xml',
        namespace='http://schemas.openxmlformats.org/presentationml/2006/main',
        element_names=('modifyVerifier', 'documentProtection'),
    ),
}


class ProtectionRemovalService:
    """Removes edit protection from a document, leaving it editable."""

    def remove(self, document: Document) -> Document:
        protection = _PROTECTION_BY_FORMAT.get(document.format)
        if protection is None:
            raise UnsupportedFormatError(document.format.value)

        updated_parts: list[PackagePart] = []
        for part in document.parts:
            if part.name == protection.part_name:
                content = self._strip_protection(part.content, protection)
                updated_parts.append(PackagePart(name=part.name, content=content))
            else:
                updated_parts.append(part)

        document.parts = updated_parts
        return document

    @staticmethod
    def _strip_protection(content: bytes, protection: EditProtection) -> bytes:
        root = ET.fromstring(content)  # noqa: S314
        parent_map = {child: parent for parent in root.iter() for child in parent}

        for element_name in protection.element_names:
            tag = f'{{{protection.namespace}}}{element_name}'
            for element in root.findall(f'.//{tag}'):
                parent = parent_map.get(element)
                if parent is not None:
                    parent.remove(element)

        result: bytes = ET.tostring(root, encoding='UTF-8', xml_declaration=True)
        return result
