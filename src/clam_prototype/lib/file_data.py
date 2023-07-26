import json
from enum import Enum
from textwrap import dedent

import humanize
import magic
import os


class FileType(Enum):
    # OVA and TAR both magic out to TAR
    TAR = (1, "tar")
    ZIP = (2, "zip")
    ISO = (3, "iso")
    VMDK = (4, "vmdk")
    TARGZ = (5, "tar.gz")
    QCOW2 = (6, "qcow2")
    UNKNOWN = (99, "unknown")

    def get_filetype_short(self):
        return self.value[1]


class FileMetadata:
    def __init__(self):
        self.path = ''
        self.desc = ''
        self.size_raw = 0
        self.filetype = FileType.UNKNOWN
        self.root_meta = None

    def get_filename(self) -> str:
        return os.path.basename(self.path)

    # Maybe don't need?
    # def as_json(self) -> str:
    #     return dedent(f'''\
    #             {{
    #                 "path": "{self.path}",
    #                 "desc": "{self.desc}",
    #                 "size": {self.size},
    #                 "filetype": "{self.filetype}"
    #             }}''')

    def __str__(self):
        return dedent(f'''\
                Path: {self.path} 
                Description: {self.desc}
                Size: {humanize.naturalsize(self.size_raw)}
                Filetype: {self.filetype}''')


def _get_filetype(desc) -> FileType:
    if desc.startswith('POSIX tar archive'):
        return FileType.TAR
    elif desc.startswith('POSIX tar archive (GNU)'):
        return FileType.TAR
    elif desc.startswith('Zip archive data'):
        return FileType.ZIP
    elif desc.startswith('ISO 9660 CD-ROM filesystem data'):
        return FileType.ISO
    elif desc.startswith('VMware4 disk image'):
        return FileType.VMDK
    elif desc.startswith('gzip compressed data'):
        return FileType.TARGZ
    elif desc.startswith('QEMU QCOW2 Image'):
        return FileType.QCOW2
    else:
        return FileType.UNKNOWN


def file_meta_from_path(path: str) -> 'FileMetadata':
    rv = FileMetadata()
    rv.path = path
    rv.desc = magic.from_file(path, mime=False)
    rv.size_raw = os.path.getsize(path)
    rv.filetype = _get_filetype(rv.desc)

    return rv


def file_meta_from_json(json_str: str) -> 'FileMetadata':
    json_obj = json.loads(json_str)
    rv = FileMetadata()

    rv.path = json_obj['path']
    rv.desc = json_obj['desc']
    rv.size_raw = json_obj['size']
    rv.filetype = json_obj['filetype']

    return rv
