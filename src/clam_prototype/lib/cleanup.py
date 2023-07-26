import glob
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
            raise click.FileError(f'Unable to dismount from {self.path}')

        shutil.rmtree(path=self.path, ignore_errors=True)


class VmdkCleanupHandler(BaseCleanupHandler):
    def __init__(self, path: str):
        super().__init__(path)

    def cleanup(self) -> None:
        raise NotImplementedError()


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


def cleanup_path(filepath: str) -> None:
    filetype = determine_filetype(filepath)

    if filetype not in FILETYPE_HANDLERS.keys():
        raise click.BadParameter(f'Unhandled file type: {filetype}')

    handler_class = FILETYPE_HANDLERS[filetype]
    handler = handler_class(filepath)
    handler.cleanup()


def cleanup_file(filepath: str) -> None:
    files = find_associated_dirs(filepath)
    if len(files) == 0:
        print(f'No associated directories found for {filepath}')

    print(f'Found an associated directorie for {filepath}')

    cleanup_path(files[0])


def cleanup_recursive(filepath: str) -> None:
    pass
