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

import glob
import os
import tempfile

from clamav_large_archive_scanner.lib.file_data import FileMetadata, FileType

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
