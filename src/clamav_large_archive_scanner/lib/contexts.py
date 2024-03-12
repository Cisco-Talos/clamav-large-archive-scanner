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

import shutil

import clamav_large_archive_scanner.lib.file_data as file_data
import clamav_large_archive_scanner.lib.tmp_files as tmp_files


class UnpackContext:
    def __init__(self, file_meta: file_data.FileMetadata, enclosing_tmp_dir: str, parent_ctx=None):
        self.file_meta = file_meta  # type: file_data.FileMetadata

        # This is the directory that will contain the temp dir for this file
        self.enclosing_tmp_dir = enclosing_tmp_dir  # type: str

        self.unpacked_dir_location = None  # type: str | None
        self.parent_ctx = parent_ctx  # type: UnpackContext | None

    def create_tmp_dir(self):
        self.unpacked_dir_location = tmp_files.make_temp_dir(self.file_meta, self.enclosing_tmp_dir)

    def cleanup_tmp(self):
        if self.unpacked_dir_location is not None:
            shutil.rmtree(self.unpacked_dir_location, ignore_errors=True)

    @staticmethod
    def _strip_tmp(u_ctx, path: str) -> str:
        if u_ctx.unpacked_dir_location is None:
            return path

        return path.replace(u_ctx.unpacked_dir_location, "")

    def nice_filename(self) -> str:
        if self.parent_ctx is None:
            return self.file_meta.get_filename()
        else:
            return f'{self.parent_ctx.nice_filename()}::{self._strip_tmp(self.parent_ctx, self.file_meta.path)}'

    def __str__(self):
        if self.unpacked_dir_location is not None:
            return f'{self.nice_filename()} -> {self.unpacked_dir_location}'
        else:
            return f'{self.nice_filename()} -> Not unpacked'

    def detmp_filepath(self, log_msg: str) -> str:
        """
        This will attempt to replace the tmp directory with the original nice filename
        :param log_msg:
        :return:
        """

        if self.unpacked_dir_location is None:
            return log_msg

        return log_msg.replace(self.unpacked_dir_location, self.nice_filename())
