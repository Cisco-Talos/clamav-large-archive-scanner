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

import click

import lib.mount_tools as mount_tools
import lib.tmp_files as tmp_files
from lib import fast_log
from lib.exceptions import MountException
from lib.file_data import FileType


class BaseCleanupHandler:
    def __init__(self, path: str):
        self.path = path

    def cleanup(self) -> None:
        fast_log.debug(f'Cleaning up {self.path} by deleting it.')
        shutil.rmtree(path=self.path, ignore_errors=True)


class TarCleanupHandler(BaseCleanupHandler):
    def __init__(self, path: str):
        super().__init__(path)


class ZipCleanupHandler(BaseCleanupHandler):
    def __init__(self, path: str):
        super().__init__(path)


class IsoCleanupHandler(BaseCleanupHandler):
    def __init__(self, path: str):
        super().__init__(path)

    def cleanup(self) -> None:
        fast_log.debug(f'Cleaning up {self.path} by un-mounting it.')
        try:
            mount_tools.umount_iso(self.path)
        except MountException as e:
            raise click.FileError(filename=self.path, hint=f'Unable to un-mount from {self.path}')

        shutil.rmtree(path=self.path, ignore_errors=True)


# Handles VMDK and QCOW2
class GuestFSCleanupHandler(BaseCleanupHandler):
    def __init__(self, path: str):
        super().__init__(path)

    def cleanup(self) -> None:
        fast_log.debug(f'Cleaning up {self.path} by un-mounting it all underlying partitions')

        # Find all mount-points in the directory
        dirs = mount_tools.list_top_level_dirs(self.path)
        all_success = True

        for a_dir in dirs:
            try:
                fast_log.debug(f'Un-mounting {a_dir}')
                mount_tools.umount_guestfs_partition(a_dir)
            except MountException as e:
                fast_log.warn(f'Unable to unmount {a_dir}, continuing anyway')
                fast_log.warn(f'Got the following mount error: {e}')
                all_success = False
                continue

        if all_success:
            shutil.rmtree(path=self.path, ignore_errors=True)
        else:
            fast_log.warn('Unable to un-mount all partitions')


class TarGzCleanupHandler(BaseCleanupHandler):
    def __init__(self, path: str):
        super().__init__(path)


FILETYPE_HANDLERS = {
    FileType.TAR: TarCleanupHandler,
    FileType.ZIP: ZipCleanupHandler,
    FileType.ISO: IsoCleanupHandler,
    FileType.VMDK: GuestFSCleanupHandler,
    FileType.TARGZ: TarGzCleanupHandler,
    FileType.QCOW2: GuestFSCleanupHandler,
}


def _cleanup_file(filepath: str, only_one: bool, tmp_dir: str) -> None:
    files = tmp_files.find_associated_dirs(filepath, tmp_dir)
    if len(files) == 0:
        fast_log.debug(f'No associated directories found for {filepath}')
        return

    if only_one:
        fast_log.debug(f'Found an associated directory for {filepath}')
        cleanup_path(files[0])
    else:
        fast_log.debug(f'Found {len(files)} associated directories for {filepath}')
        for file in files:
            fast_log.debug(f'Cleaning up {file}')
            cleanup_path(file)


def cleanup_path(filepath: str) -> None:
    filetype = tmp_files.determine_tmp_dir_filetype(filepath)

    if filetype not in FILETYPE_HANDLERS.keys():
        raise click.BadParameter(f'Unhandled file type: {filetype}')

    handler_class = FILETYPE_HANDLERS[filetype]
    handler = handler_class(filepath)
    handler.cleanup()


def cleanup_file(filepath: str, tmp_dir: str) -> None:
    _cleanup_file(filepath, only_one=True, tmp_dir=tmp_dir)


def cleanup_recursive(filepath: str, tmp_dir: str) -> None:
    _cleanup_file(filepath, only_one=False, tmp_dir=tmp_dir)
