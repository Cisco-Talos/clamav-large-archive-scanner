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


import os
import shutil

import click

from lib import fast_log
from lib.exceptions import ArchiveException, MountException
from lib.fast_log import trace

# These imports are here to make mocking easier in UT
# Yes, it does make the code a bit more verbose, but it's worth it
import lib.file_data as file_data
import lib.mount_tools as mount_tools
import lib.contexts as contexts


class BaseFileUnpackHandler:
    def __init__(self, u_ctx: contexts.UnpackContext):
        self.u_ctx = u_ctx
        self.u_ctx.create_tmp_dir()

    def unpack(self) -> contexts.UnpackContext:
        raise NotImplementedError()


class ArchiveFileUnpackHandler(BaseFileUnpackHandler):
    def __init__(self, u_ctx: contexts.UnpackContext, file_format: str):
        super().__init__(u_ctx)
        self.format = file_format

    def unpack(self) -> contexts.UnpackContext:
        # This can sometimes fail if the archive is corrupt
        try:
            shutil.unpack_archive(self.u_ctx.file_meta.path, self.u_ctx.unpacked_dir_location, format=self.format)
        except Exception as e:
            # Delete the temp dir since the unpacker created it
            self.u_ctx.cleanup_tmp()
            raise ArchiveException(e)

        return self.u_ctx


class IsoFileUnpackHandler(BaseFileUnpackHandler):
    def __init__(self, u_ctx: contexts.UnpackContext):
        super().__init__(u_ctx)

    def unpack(self) -> contexts.UnpackContext:
        try:
            mount_tools.mount_iso(self.u_ctx.file_meta.path, self.u_ctx.unpacked_dir_location)
        except MountException as e:
            fast_log.debug(f'Got MountException {e} when trying to mount {self.u_ctx.file_meta.path} to {self.u_ctx.unpacked_dir_location}')
            raise click.FileError(filename=self.u_ctx.file_meta.path, hint=f'Unable to mount {self.u_ctx.file_meta.path} to {self.u_ctx.unpacked_dir_location}')

        return self.u_ctx


class TarFileUnpackHandler(ArchiveFileUnpackHandler):
    def __init__(self, u_ctx: contexts.UnpackContext):
        super().__init__(u_ctx, 'tar')


class ZipFileUnpackHandler(ArchiveFileUnpackHandler):
    def __init__(self, u_ctx: contexts.UnpackContext):
        super().__init__(u_ctx, 'zip')


class TarGzFileUnpackHandler(ArchiveFileUnpackHandler):
    def __init__(self, u_ctx: contexts.UnpackContext):
        super().__init__(u_ctx, 'gztar')


# Handles VMDK and QCOW2
class GuestFSFileUnpackHandler(BaseFileUnpackHandler):
    def __init__(self, u_ctx: contexts.UnpackContext):
        super().__init__(u_ctx)

    def unpack(self) -> contexts.UnpackContext:
        try:
            # These VM Filesystem images can have multiple partitions
            # These need to be mounted individually
            partitions = mount_tools.enumerate_guestfs_partitions(
                self.u_ctx.file_meta.path)  # internal partitions inside the blob

            fast_log.debug(f'Found the following partitions:')
            fast_log.debug('\n'.join(partitions))

        except MountException as e:
            fast_log.debug(f'Unable to list partitions for {self.u_ctx.file_meta.path}, aborting unpack')
            fast_log.debug(f'Got the following error: {e}')

            raise click.FileError(filename=self.u_ctx.file_meta.path,
                                  hint=f'Unable to list partitions for {self.u_ctx.file_meta.path}, aborting unpack')

        for partition in partitions:
            try:
                fast_log.debug(f'attempting to mount {partition}')
                mount_tools.mount_guestfs_partition(self.u_ctx.file_meta.path, partition, self.u_ctx.unpacked_dir_location)
                fast_log.debug(f'Mounted {partition} to {self.u_ctx.unpacked_dir_location}')
            except MountException as e:
                fast_log.warn(f'Unable to mount the {partition} for {self.u_ctx.file_meta.path}, attempting to continue anyway')
                fast_log.debug(f'Got the following error: {e}')

        return self.u_ctx


# Directories don't need unpacked, this just fits it into the same pattern
class DirFileUnpackHandler:
    def __init__(self, u_ctx: contexts.UnpackContext):
        self.u_ctx = u_ctx

    def unpack(self) -> contexts.UnpackContext:
        return self.u_ctx


FILETYPE_HANDLERS = {
    file_data.FileType.TAR: TarFileUnpackHandler,
    file_data.FileType.ISO: IsoFileUnpackHandler,
    file_data.FileType.VMDK: GuestFSFileUnpackHandler,
    file_data.FileType.ZIP: ZipFileUnpackHandler,
    file_data.FileType.TARGZ: TarGzFileUnpackHandler,
    file_data.FileType.QCOW2: GuestFSFileUnpackHandler,
    file_data.FileType.DIR: DirFileUnpackHandler,
}

HANDLED_FILE_TYPES = FILETYPE_HANDLERS.keys()


def _handler_from_ctx(u_ctx: contexts.UnpackContext) -> BaseFileUnpackHandler:
    handler_class = FILETYPE_HANDLERS[u_ctx.file_meta.filetype]
    return handler_class(u_ctx)


def is_handled_filetype(file_meta: file_data.FileMetadata) -> bool:
    return file_meta.filetype in HANDLED_FILE_TYPES


def _do_unpack(u_ctx: contexts.UnpackContext) -> contexts.UnpackContext:
    fast_log.debug('Doing unpack')
    if not is_handled_filetype(u_ctx.file_meta):
        raise click.BadParameter(f'Unhandled file type: {u_ctx.file_meta.filetype}')

    handler = _handler_from_ctx(u_ctx)
    ret_ctx = handler.unpack()

    return ret_ctx


def unpack(file: file_data.FileMetadata, tmp_dir: str) -> contexts.UnpackContext:
    try:
        u_ctx = contexts.UnpackContext(file, tmp_dir)
        return _do_unpack(u_ctx)
    except ArchiveException as e:
        raise click.FileError(filename=file.path, hint=f'Unable to unpack {file.path}, got the following error: {e}')


def unpack_recursive(parent_filemeta: file_data.FileMetadata, min_file_size: int, tmp_dir: str) -> list[contexts.UnpackContext]:
    unpacked_ctx = list()  # type: list[contexts.UnpackContext]

    parent_ctx = contexts.UnpackContext(parent_filemeta, tmp_dir)
    parent_ctx = _do_unpack(parent_ctx)

    unpacked_ctx.append(parent_ctx)

    ctxs_to_inspect = [parent_ctx]  # type: list[contexts.UnpackContext]

    # Now walk the unpacked directory and find all relevant archives
    # Add found archives to inspection list
    # Go until all archives are unpacked and inspected
    while len(ctxs_to_inspect) > 0:
        ctx_to_inspect = ctxs_to_inspect.pop()
        fast_log.debug(f'Analyzing {ctx_to_inspect.nice_filename()} for additional archives')
        for root, _, files in os.walk(ctx_to_inspect.unpacked_dir_location):
            trace(f'Looking at {root}')
            for file in files:
                file_path = os.path.join(root, file)
                trace(f'Looking at at {file_path}')
                file_meta = file_data.file_meta_from_path(file_path)

                a_new_ctx = contexts.UnpackContext(file_meta, tmp_dir, parent_ctx=ctx_to_inspect)

                trace(f'Got meta from at {file_path}, type is {file_meta.filetype}')

                if not is_handled_filetype(file_meta) or file_meta.size_raw < min_file_size:
                    trace('File too small or not handled, moving on')
                    # During recursive unpacking, we need to warn the user if we found a file that was not handled
                    # But meets the filesize requirement
                    if file_meta.size_raw >= min_file_size:
                        fast_log.warn(f'Ignoring unhandled large file: {file_path}')
                    continue

                # Current is a valid unpackable archive
                fast_log.debug(f'Found archive:')
                fast_log.debug(str(file_meta))
                file_meta.root_meta = parent_filemeta

                try:

                    a_new_ctx = _do_unpack(a_new_ctx)
                    unpacked_ctx.append(a_new_ctx)
                    ctxs_to_inspect.append(a_new_ctx)
                except ArchiveException as e:
                    fast_log.warn(f'Unable to unpack {file_path}, got the following error: {e}. Continuing anyway')

    return unpacked_ctx
