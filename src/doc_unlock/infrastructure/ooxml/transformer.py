"""Streaming OOXML package transformer."""

import shutil
import zipfile
from typing import TYPE_CHECKING, override

from doc_unlock.domain.ports import PackageTransformer

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import BinaryIO


class ZipPackageTransformer(PackageTransformer):
    """Rewrites a package stream, transforming only the protection part."""

    @override
    def transform(
        self,
        source: BinaryIO,
        destination: BinaryIO,
        target_part: str,
        transform_part: Callable[[bytes], bytes],
    ) -> None:
        with zipfile.ZipFile(source) as zin, zipfile.ZipFile(destination, 'w') as zout:
            for info in zin.infolist():
                if info.is_dir():
                    continue
                out_info = self._new_info(info)
                if info.filename == target_part:
                    content = transform_part(zin.read(info.filename))
                    zout.writestr(out_info, content)
                else:
                    with zin.open(info) as src, zout.open(out_info, 'w') as dst:
                        shutil.copyfileobj(src, dst)

    @staticmethod
    def _new_info(info: zipfile.ZipInfo) -> zipfile.ZipInfo:
        out = zipfile.ZipInfo(filename=info.filename, date_time=info.date_time)
        out.compress_type = info.compress_type
        out.external_attr = info.external_attr
        out.comment = info.comment
        return out
