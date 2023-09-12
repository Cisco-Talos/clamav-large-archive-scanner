import os
import shutil

import click

from lib.exceptions import ArchiveException, MountException
from lib.fast_log import fast_log

# These imports are here to make mocking easier in UT
# Yes, it does make the code a bit more verbose, but it's worth it
import lib.file_data as file_data
import lib.mount_tools as mount_tools
import lib.tmp_files as tmp_files


class BaseFileUnpackHandler:
    def __init__(self, file_meta: file_data.FileMetadata, tmp_dir_parent: str):
        self.file_meta = file_meta
        self.tmp_dir = tmp_files.make_temp_dir(self.file_meta, tmp_dir_parent)

    def unpack(self) -> str:
        raise NotImplementedError()


class ArchiveFileUnpackHandler(BaseFileUnpackHandler):
    def __init__(self, file_meta: file_data.FileMetadata, file_format: str, tmp_dir_parent: str):
        super().__init__(file_meta, tmp_dir_parent)
        self.format = file_format

    def unpack(self) -> str:
        # This can sometimes fail if the archive is corrupt
        try:
            shutil.unpack_archive(self.file_meta.path, self.tmp_dir, format=self.format)
        except Exception as e:
            # Delete the temp dir since the unpacker created it
            shutil.rmtree(self.tmp_dir, ignore_errors=True)
            raise ArchiveException(e)

        return self.tmp_dir


class IsoFileUnpackHandler(BaseFileUnpackHandler):
    def __init__(self, file_meta: file_data.FileMetadata, tmp_dir_parent: str):
        super().__init__(file_meta, tmp_dir_parent)

    def unpack(self) -> str:
        try:
            mount_tools.mount_iso(self.file_meta.path, self.tmp_dir)
        except MountException as e:
            # TODO: Log the error from subprocess?
            raise click.FileError(filename=self.file_meta.path, hint=f'Unable to mount {self.file_meta.path} to {self.tmp_dir}')

        return self.tmp_dir


class TarFileUnpackHandler(ArchiveFileUnpackHandler):
    def __init__(self, file_meta: file_data.FileMetadata, tmp_dir_parent: str):
        super().__init__(file_meta, 'tar', tmp_dir_parent)


class ZipFileUnpackHandler(ArchiveFileUnpackHandler):
    def __init__(self, file_meta: file_data.FileMetadata, tmp_dir_parent: str):
        super().__init__(file_meta, 'zip', tmp_dir_parent)


class TarGzFileUnpackHandler(ArchiveFileUnpackHandler):
    def __init__(self, file_meta: file_data.FileMetadata, tmp_dir_parent: str):
        super().__init__(file_meta, 'gztar', tmp_dir_parent)


# Handles VMDK and QCOW2
class GuestFSFileUnpackHandler(BaseFileUnpackHandler):
    def __init__(self, file_meta: file_data.FileMetadata, tmp_dir_parent: str):
        super().__init__(file_meta, tmp_dir_parent)

    def unpack(self) -> str:
        try:
            # These VM Filesystem images can have multiple partitions
            # These need to be mounted individually
            partitions = mount_tools.enumerate_guestfs_partitions(
                self.file_meta.path)  # internal partitions inside the blob

            print(f'Found the following partitions:')
            print('\n'.join(partitions))

        except MountException as e:
            # TODO: Log the error from subprocess?
            raise click.FileError(filename=self.file_meta.path,
                                  hint=f'Unable to list partitions for {self.file_meta.path}, aborting unpack')

        for partition in partitions:
            try:
                print(f'attempting to mount {partition}')
                mount_tools.mount_guestfs_partition(self.file_meta.path, partition, self.tmp_dir)
                print(f'Mounted {partition} to {self.tmp_dir}')
            except MountException as e:
                # TODO: Log the error from subprocess?
                print(f'Unable to mount the {partition} for {self.file_meta.path}, attempting to continue anyway')

        return self.tmp_dir


# Directories don't need unpacked, this just fits it into the same pattern
class DirFileUnpackHandler:
    def __init__(self, file_meta: file_data.FileMetadata, tmp_dir=''):
        self.file_meta = file_meta
        # tmp_dir is ignored, this is just to match the BaseFileUnpackHandler

    def unpack(self) -> str:
        return self.file_meta.path


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


def _handler_from_file_meta(file_meta: file_data.FileMetadata, tmp_dir: str) -> BaseFileUnpackHandler:
    handler_class = FILETYPE_HANDLERS[file_meta.filetype]
    return handler_class(file_meta, tmp_dir)


def is_handled_filetype(filetype: file_data.FileType) -> bool:
    return filetype in HANDLED_FILE_TYPES


def _do_unpack(file: file_data.FileMetadata, tmp_dir: str) -> str:
    print("Doing unpack")
    if not is_handled_filetype(file.filetype):
        raise click.BadParameter(f'Unhandled file type: {file.filetype}')

    handler = _handler_from_file_meta(file, tmp_dir)
    dest_dir = handler.unpack()

    return dest_dir


def unpack(file: file_data.FileMetadata, tmp_dir: str) -> str:
    try:
        return _do_unpack(file, tmp_dir)
    except ArchiveException as e:
        raise click.FileError(filename=file.path, hint=f'Unable to unpack {file.path}, got the following error: {e}')


def unpack_recursive(parent_file: file_data.FileMetadata, min_file_size: int, tmp_dir: str) -> list[str]:
    unpacked_dirs = list()

    parent_unpack_dir = _do_unpack(parent_file, tmp_dir)

    unpacked_dirs.append(parent_unpack_dir)

    dirs_to_inspect = [parent_unpack_dir]

    # Now walk the unpacked directory and find all relevant archives
    # Add found archives to inspection list
    # Go until all archives are unpacked and inspected
    while len(dirs_to_inspect) > 0:
        current_dir = dirs_to_inspect.pop()
        print(f'Analyzing {current_dir} for additional archives')
        for root, _, files in os.walk(current_dir):
            fast_log(f'Looking at {root}')
            for file in files:
                file_path = os.path.join(root, file)
                fast_log(f'Looking at at {file_path}')
                file_meta = file_data.file_meta_from_path(file_path)

                fast_log(f'Got meta from at {file_path}, type is {file_meta.filetype}')

                if not is_handled_filetype(file_meta.filetype) or file_meta.size_raw < min_file_size:
                    fast_log('File too small or not handled, moving on')
                    continue

                # Current is a valid unpackable archive
                print(f'Found archive:')
                print(file_meta)
                file_meta.root_meta = parent_file

                try:
                    unpack_dir = _do_unpack(file_meta, tmp_dir)
                    unpacked_dirs.append(unpack_dir)
                    dirs_to_inspect.append(unpack_dir)
                except ArchiveException as e:
                    print(f'Unable to unpack {file_path}, got the following error: {e}. Continuing anyway')

    return unpacked_dirs
