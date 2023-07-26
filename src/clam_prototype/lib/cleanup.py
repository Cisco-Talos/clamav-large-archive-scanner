import glob
import os
import shutil
import subprocess

import click

from lib.file_data import FileMetadata, FileType
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
        result = subprocess.run(['umount', self.path])
        if result.returncode != 0:
            raise click.FileError(f'Unable to un-mount from {self.path}')

        shutil.rmtree(path=self.path, ignore_errors=True)


class VmdkCleanupHandler(BaseCleanupHandler):
    def __init__(self, path: str):
        super().__init__(path)

    @staticmethod
    def _umount_partition( directory: str) -> bool:
        print(f'Un-mounting {directory}')
        rv = True
        # guestunmount local_dir
        result = subprocess.run(['guestunmount', directory])
        if result.returncode != 0:
            print(f'Unable to unmount {directory}, continuing anyway')
            rv = False

        return rv

    def cleanup(self) -> None:
        print(f'Cleaning up {self.path} by un-mounting it all underlying partitions')

        dirs = []
        for a_dir in os.listdir(self.path):
            full_path = os.path.join(self.path, a_dir)
            if os.path.isdir(full_path):
                dirs.append(full_path)

        success = True

        for a_dir in dirs:
            success &= self._umount_partition(a_dir)

        if success:
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
    FileType.VMDK: VmdkCleanupHandler,
    FileType.TARGZ: TarGzCleanupHandler,
}


def _cleanup_file(filepath: str, only_one: bool) -> None:
    files = find_associated_dirs(filepath)
    if len(files) == 0:
        print(f'No associated directories found for {filepath}')

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
