import shutil
import subprocess

import click

from lib.file_data import FileMetadata, FileType
from lib.tmp_files import determine_filetype


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
        result = subprocess.run(['umount', self.path])
        if result.returncode != 0:
            raise click.FileError(f'Unable to dismount from {self.path}')


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


def cleanup(filepath: str) -> None:
    filetype = determine_filetype(filepath)

    if filetype not in FILETYPE_HANDLERS.keys():
        raise click.BadParameter(f'Unhandled file type: {filetype}')

    handler_class = FILETYPE_HANDLERS[filetype]
    handler = handler_class(filepath)
    handler.cleanup()
