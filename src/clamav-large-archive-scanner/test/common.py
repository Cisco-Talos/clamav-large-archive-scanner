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

from lib import fast_log
from lib.contexts import UnpackContext
from lib.file_data import FileMetadata


def init_logging():
    fast_log.log_start(enable_verbose=True, enable_trace=False)


def make_file_meta(path: str) -> FileMetadata:
    meta = FileMetadata()
    meta.path = path

    return meta


def make_basic_unpack_ctx(unpack_dir: str, file_path: str) -> UnpackContext:
    meta = make_file_meta(file_path)
    ctx = UnpackContext(file_meta=meta, enclosing_tmp_dir='/tmp')
    ctx.unpacked_dir_location = unpack_dir

    return ctx
