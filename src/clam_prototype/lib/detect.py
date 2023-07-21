from enum import Enum
from textwrap import dedent

import magic
import os


class FileType(Enum):
    # OVA and TAR both magic out to TAR
    TAR = 1
    ZIP = 2
    ISO = 3
    VMDK = 4
    UNKNOWN = 5


class FileMetadata:
    def __init__(self, path: str):
        self.path = path
        self.desc = magic.from_file(path, mime=False)
        self.size = os.path.getsize(path)
        self.filetype = self._get_filetype()

    def _get_filetype(self) -> FileType:
        if self.desc.startswith('POSIX tar archive'):
            return FileType.TAR
        elif self.desc.startswith('POSIX tar archive (GNU)'):
            return FileType.TAR
        elif self.desc.startswith('Zip archive data'):
            return FileType.ZIP
        elif self.desc.startswith('ISO 9660 CD-ROM filesystem data'):
            return FileType.ISO
        elif self.desc.startswith('VMware4 disk image'):
            return FileType.VMDK
        else:
            return FileType.UNKNOWN

    def __str__(self):
        return dedent(f'''\
                Path: {self.path} 
                Description: {self.desc}
                Size: {self.size} bytes)
                Filetype: {self.filetype}''')


def get_metadata(path: str) -> FileMetadata:
    return FileMetadata(path)
