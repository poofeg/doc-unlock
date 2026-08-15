"""Domain services: pure business logic."""

import xml.etree.ElementTree as ET  # noqa: S405

from .exceptions import UnsupportedFormatError
from .models import DocumentFormat, EditProtection

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
    """Knows where protection lives per format and strips it from a single XML part."""

    @staticmethod
    def protection_for(format: DocumentFormat) -> EditProtection:
        protection = _PROTECTION_BY_FORMAT.get(format)
        if protection is None:
            raise UnsupportedFormatError(format.value)
        return protection

    @staticmethod
    def strip(content: bytes, protection: EditProtection) -> bytes:
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
