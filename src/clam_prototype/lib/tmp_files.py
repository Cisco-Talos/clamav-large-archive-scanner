#  Copyright (C) 2023 Cisco Systems, Inc. and/or its affiliates. All rights reserved.
#
#  Authors: Dave Zhu (yanbzhu@cisco.com)
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License version 2 as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

import glob
import os
import tempfile

from lib.file_data import FileMetadata, FileType

TMP_DIR_PREFIX = 'clam_unpacker'


# Makes a temporary directory for the file to be unpacked into, named base on filetype and filename
def make_temp_dir(file_meta: FileMetadata, tmp_dir: str) -> str:
    if not file_meta.root_meta:
        prefix = f'{TMP_DIR_PREFIX}_{file_meta.filetype.get_filetype_short()}_{file_meta.get_filename()}_'
    else:
        prefix = f'{TMP_DIR_PREFIX}_{file_meta.filetype.get_filetype_short()}-p_{file_meta.root_meta.get_filename()}_p-{file_meta.get_filename()}_'
    tmp_dir = tempfile.mkdtemp(prefix=prefix, dir=tmp_dir)

    # Need to make it readable by everyone, otherwise clam will throw a fit
    os.chmod(tmp_dir, 0o755)

    return tmp_dir


# Determine the filetype based on the path, assuming that it was created by make_temp_dir
def determine_tmp_dir_filetype(path: str) -> FileType:
    for filetype in FileType:
        if os.path.basename(path).startswith(f'{TMP_DIR_PREFIX}_{filetype.get_filetype_short()}'):
            return filetype

    return FileType.UNKNOWN


# Find all the directories created by make_temp_dir that are associated with the given file
def find_associated_dirs(filepath: str, tmp_dir: str) -> list[str]:
    file_name = os.path.basename(filepath)
    return glob.glob(f'{tmp_dir}/{TMP_DIR_PREFIX}_*_{file_name}_*')
