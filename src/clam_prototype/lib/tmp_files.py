import glob
import os
import tempfile

from lib.file_data import FileMetadata, FileType


# Makes a temporary directory for the file to be unpacked into, named base on filetype and filename
def make_temp_dir(file_meta: FileMetadata) -> str:
    prefix = f'clam_unpacker_{file_meta.filetype.get_filetype_short()}_{file_meta.get_filename()}_'
    tmp_dir = tempfile.mkdtemp(prefix=prefix, dir='/tmp')

    return tmp_dir


# Determine the filetype based on the path, assuming that it was created by make_temp_dir
def determine_filetype(path: str) -> FileType:
    for filetype in FileType:
        if os.path.basename(path).startswith(f'clam_unpacker_{filetype.get_filetype_short()}'):
            return filetype

    return FileType.UNKNOWN


def find_associated_dirs(filepath: str) -> list[str]:
    file_name = os.path.basename(filepath)
    return glob.glob(f'/tmp/clam_unpacker_*_{file_name}_*')