import os
import shutil

import click

from lib.file_data import FileType
from lib.mount_tools import umount_iso, MountException, umount_guestfs_partition
from lib.tmp_files import determine_filetype, find_associated_dirs


class BaseCleanupHandler:
    def __init__(self, path: str):
        self.path = path

    def cleanup(self) -> None:
        print(f'Cleaning up {self.path} by deleting it.')
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
        print(f'Cleaning up {self.path} by un-mounting it.')
        try:
            umount_iso(self.path)
        except MountException as e:
            raise click.FileError(f'Unable to un-mount from {self.path}')

        shutil.rmtree(path=self.path, ignore_errors=True)


# Handles VMDK and QCOW2
class GuestFSCleanupHandler(BaseCleanupHandler):
    def __init__(self, path: str):
        super().__init__(path)

    def cleanup(self) -> None:
        print(f'Cleaning up {self.path} by un-mounting it all underlying partitions')

        # Find all mount-points in the directory
        dirs = []
        for a_dir in os.listdir(self.path):
            full_path = os.path.join(self.path, a_dir)
            if os.path.isdir(full_path):
                dirs.append(full_path)

        all_success = True

        for a_dir in dirs:
            try:
                print(f'Un-mounting {a_dir}')
                umount_guestfs_partition(a_dir)
            except MountException as e:
                print(f'Unable to unmount {a_dir}, continuing anyway')
                print(f'Got the following mount error: {e}')
                all_success = False
                continue

        if all_success:
            shutil.rmtree(path=self.path, ignore_errors=True)
        else:
            print('Unable to un-mount all partitions')


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


def _cleanup_file(filepath: str, only_one: bool) -> None:
    files = find_associated_dirs(filepath)
    if len(files) == 0:
        print(f'No associated directories found for {filepath}')
        return

    if only_one:
        print(f'Found an associated directory for {filepath}')
        cleanup_path(files[0])
    else:
        print(f'Found {len(files)} associated directories for {filepath}')
        print(files)
        for file in files:
            cleanup_path(file)


def cleanup_path(filepath: str) -> None:
    filetype = determine_filetype(filepath)

    if filetype not in FILETYPE_HANDLERS.keys():
        raise click.BadParameter(f'Unhandled file type: {filetype}')

    handler_class = FILETYPE_HANDLERS[filetype]
    handler = handler_class(filepath)
    handler.cleanup()


def cleanup_file(filepath: str) -> None:
    _cleanup_file(filepath, only_one=True)


def cleanup_recursive(filepath: str) -> None:
    _cleanup_file(filepath, only_one=False)
