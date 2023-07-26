import shutil
import subprocess
import tempfile

import click

from lib.detect import FileMetadata, FileType

HANDLED_FILETYPES = [
    FileType.ISO,
    FileType.TAR,
    FileType.VMDK,
    FileType.ZIP,
    FileType.TARGZ
]


class BaseFileUnpackHandler:
    def __init__(self, file_meta: FileMetadata):
        self.file_meta = file_meta
        self.tmp_dir = self._make_temp_dir()

    def unpack(self) -> str:
        raise NotImplementedError()

    def _make_temp_dir(self) -> str:
        prefix = f'clam_unpacker_{self.file_meta.filetype.get_filetype_short()}_{self.file_meta.get_filename()}_'
        tmp_dir = tempfile.mkdtemp(prefix=prefix, dir='/tmp')

        return tmp_dir


class IsoFileUnpackHandler(BaseFileUnpackHandler):
    def __init__(self, file_meta: FileMetadata):
        super().__init__(file_meta)

    def unpack(self) -> str:
        result = subprocess.run(['mount', '-r', '-o', 'loop', self.file_meta.path, self.tmp_dir])
        if result.returncode != 0:
            raise click.FileError(f'Unable to mount {self.file_meta.path} to {self.tmp_dir}')

        return self.tmp_dir


class TarFileUnpackHandler(BaseFileUnpackHandler):
    def __init__(self, file_meta: FileMetadata):
        super().__init__(file_meta)

    def unpack(self) -> str:
        shutil.unpack_archive(self.file_meta.path, self.tmp_dir, format='tar')

        return self.tmp_dir


class VmdkFileUnpackHandler(BaseFileUnpackHandler):
    def __init__(self, file_meta: FileMetadata):
        super().__init__(file_meta)

    def unpack(self) -> str:
        raise NotImplementedError()


class ZipFileUnpackHandler(BaseFileUnpackHandler):
    def __init__(self, file_meta: FileMetadata):
        super().__init__(file_meta)

    def unpack(self) -> str:
        shutil.unpack_archive(self.file_meta.path, self.tmp_dir, format='zip')

        return self.tmp_dir


class TarGzFileUnpackHandler(BaseFileUnpackHandler):
    def __init__(self, file_meta: FileMetadata):
        super().__init__(file_meta)

    def unpack(self) -> str:
        shutil.unpack_archive(self.file_meta.path, self.tmp_dir, format='gztar')

        return self.tmp_dir


def _clean_temp_dir(temp_dir: str):
    shutil.rmtree(path=temp_dir, ignore_errors=True)


def unmount_iso(self, mount_dir: str) -> None:
    result = subprocess.run(['umount', mount_dir])
    if result.returncode != 0:
        raise click.FileError(f'Unable to dismount from {mount_dir}')


def handler_from_file_meta(file_meta: FileMetadata) -> BaseFileUnpackHandler:
    if file_meta.filetype == FileType.TAR:
        return TarFileUnpackHandler(file_meta)
    elif file_meta.filetype == FileType.ISO:
        return IsoFileUnpackHandler(file_meta)
    elif file_meta.filetype == FileType.VMDK:
        return VmdkFileUnpackHandler(file_meta)
    elif file_meta.filetype == FileType.ZIP:
        return ZipFileUnpackHandler(file_meta)
    elif file_meta.filetype == FileType.TARGZ:
        return TarGzFileUnpackHandler(file_meta)
    else:
        raise NotImplementedError()


def _is_handled_filetype(filetype: FileType) -> bool:
    return filetype in HANDLED_FILETYPES


def _do_unpack(file: FileMetadata) -> str:
    print("Doing unpack")
    # Make a temp dir to work with
    if not _is_handled_filetype(file.filetype):
        raise click.BadParameter(f'Unhandled file type: {file.filetype}')

    handler = handler_from_file_meta(file)
    dest_dir = handler.unpack()

    return dest_dir


def cleanup(file: FileMetadata) -> None:
    pass


def unpack(file: FileMetadata) -> str:
    return _do_unpack(file)


def unpack_recursive(file: FileMetadata) -> list[str]:
    pass
