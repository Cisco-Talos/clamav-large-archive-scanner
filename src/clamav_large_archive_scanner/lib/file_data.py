# Copyright (C) 2023-2024 Cisco Systems, Inc. and/or its affiliates. All rights reserved.
#
# Authors: Dave Zhu (yanbzhu@cisco.com)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of mosquitto nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import stat
from enum import Enum
from textwrap import dedent

import humanize
import magic


class FileType(Enum):
    # OVA and TAR both magic out to TAR
    TAR = (1, 'tar')
    ZIP = (2, 'zip')
    ISO = (3, 'iso')
    VMDK = (4, 'vmdk')
    TARGZ = (5, 'tgz')  # This cannot be tar.gz, since that would conflict with tar during detection
    QCOW2 = (6, 'qcow2')

    # Directories don't need unpacked, this just fits it into the same pattern
    DIR = (97, 'dir')

    # These are not really filetypes, but are here as a convenience
    DOES_NOT_EXIST = (98, 'does_not_exist')  # file_meta_from_path can be called on broken symlinks
    UNKNOWN = (99, 'unknown')

    def get_filetype_short(self):
        return self.value[1]


# A data class to store metadata, plus some pretty printing
class FileMetadata:
    def __init__(self):
        self.path = ''
        self.desc = ''
        self.size_raw = 0
        self.filetype = FileType.UNKNOWN
        self.root_meta = None

    def get_filename(self) -> str:
        return os.path.basename(self.path)

    def __str__(self):
        return dedent(f'''\
                Path: {self.path} 
                Description: {self.desc}
                Size: {humanize.naturalsize(self.size_raw, binary=True)}
                Filetype: {self.filetype.get_filetype_short()}''')


DIRECTORY_DESC = 'Directory'
UNKNOWN_DESC = 'Unknown file type'
DNE_DESC = 'File does not exist'


def _get_filetype(desc) -> FileType:
    if desc.startswith('POSIX tar archive'):
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


def _is_regular_file(path: str) -> bool:
    s = os.lstat(path).st_mode
    return stat.S_ISREG(s)


def file_meta_from_path(path: str) -> 'FileMetadata':
    rv = FileMetadata()
    rv.path = path
    # Make sure the file exists before trying to get metadata
    if os.path.exists(path):

        # Only handle regular files and directories for now
        if os.path.isdir(path):
            rv.filetype = FileType.DIR
            rv.desc = DIRECTORY_DESC
            return rv
        elif not _is_regular_file(path):
            # We can probably figure this out, but it doesn't serve a purpose right now
            rv.filetype = FileType.UNKNOWN
            rv.desc = UNKNOWN_DESC
            return rv

        rv.desc = magic.from_file(path, mime=False)
        rv.size_raw = os.path.getsize(path)
        rv.filetype = _get_filetype(rv.desc)

    else:
        rv.filetype = FileType.DOES_NOT_EXIST
        rv.desc = DNE_DESC

    return rv
