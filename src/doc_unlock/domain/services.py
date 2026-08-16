"""Domain services: pure business logic."""

from lxml import etree  # noqa: S410

from .exceptions import UnsupportedFormatError
from .models import DocumentFormat, EditProtection

# Mapping of format -> where edit protection lives and how to strip it.
_PROTECTION_BY_FORMAT: dict[DocumentFormat, EditProtection] = {
    DocumentFormat.PPTX: EditProtection(
        part_name='ppt/presentation.xml',
        namespace='http://schemas.openxmlformats.org/presentationml/2006/main',
        element_names=('modifyVerifier',),
    ),
    DocumentFormat.DOCX: EditProtection(
        part_name='word/settings.xml',
        namespace='http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        element_names=('writeProtection', 'documentProtection'),
    ),
    DocumentFormat.XLSX: EditProtection(
        part_name='xl/workbook.xml',
        namespace='http://schemas.openxmlformats.org/spreadsheetml/2006/main',
        element_names=('fileSharing', 'workbookProtection'),
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
        # Disable entity resolution and network access when parsing untrusted parts.
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        root = etree.fromstring(content, parser)

        for element_name in protection.element_names:
            tag = f'{{{protection.namespace}}}{element_name}'
            for element in root.findall(f'.//{tag}'):
                parent = element.getparent()
                if parent is not None:
                    parent.remove(element)

        result: bytes = etree.tostring(root, encoding='UTF-8', xml_declaration=True)
        return result
