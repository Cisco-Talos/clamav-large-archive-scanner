import shutil
import subprocess

import click

from lib.file_data import FileMetadata, FileType
from lib.tmp_files import make_temp_dir


class BaseFileUnpackHandler:
    def __init__(self, file_meta: FileMetadata):
        self.file_meta = file_meta
        self.tmp_dir = make_temp_dir(self.file_meta)

    def unpack(self) -> str:
        raise NotImplementedError()


class ArchiveFileUnpackHandler(BaseFileUnpackHandler):
    def __init__(self, file_meta: FileMetadata, file_format: str):
        super().__init__(file_meta)
        self.format = file_format

    def unpack(self) -> str:
        shutil.unpack_archive(self.file_meta.path, self.tmp_dir, format=self.format)

        return self.tmp_dir


class IsoFileUnpackHandler(BaseFileUnpackHandler):
    def __init__(self, file_meta: FileMetadata):
        super().__init__(file_meta)

    def unpack(self) -> str:
        result = subprocess.run(['mount', '-r', '-o', 'loop', self.file_meta.path, self.tmp_dir])
        if result.returncode != 0:
            raise click.FileError(f'Unable to mount {self.file_meta.path} to {self.tmp_dir}')

        return self.tmp_dir


class TarFileUnpackHandler(ArchiveFileUnpackHandler):
    def __init__(self, file_meta: FileMetadata):
        super().__init__(file_meta, 'tar')


class VmdkFileUnpackHandler(BaseFileUnpackHandler):
    def __init__(self, file_meta: FileMetadata):
        super().__init__(file_meta)

    def unpack(self) -> str:
        raise NotImplementedError()


class ZipFileUnpackHandler(ArchiveFileUnpackHandler):
    def __init__(self, file_meta: FileMetadata):
        super().__init__(file_meta, 'zip')


class TarGzFileUnpackHandler(ArchiveFileUnpackHandler):
    def __init__(self, file_meta: FileMetadata):
        super().__init__(file_meta, 'gztar')


FILETYPE_HANDLERS = {
    FileType.TAR: TarFileUnpackHandler,
    FileType.ISO: IsoFileUnpackHandler,
    FileType.VMDK: VmdkFileUnpackHandler,
    FileType.ZIP: ZipFileUnpackHandler,
    FileType.TARGZ: TarGzFileUnpackHandler,
}


def _handler_from_file_meta(file_meta: FileMetadata) -> BaseFileUnpackHandler:
    handler_class = FILETYPE_HANDLERS[file_meta.filetype]
    return handler_class(file_meta)


def is_handled_filetype(filetype: FileType) -> bool:
    return filetype in FILETYPE_HANDLERS.keys()


def _do_unpack(file: FileMetadata) -> str:
    print("Doing unpack")
    if not is_handled_filetype(file.filetype):
        raise click.BadParameter(f'Unhandled file type: {file.filetype}')

    handler = _handler_from_file_meta(file)
    dest_dir = handler.unpack()

    return dest_dir


def unpack(file: FileMetadata) -> str:
    return _do_unpack(file)


def unpack_recursive(file: FileMetadata) -> list[str]:
    pass
