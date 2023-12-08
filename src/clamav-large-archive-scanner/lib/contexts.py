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

import shutil

import lib.file_data as file_data
import lib.tmp_files as tmp_files


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
