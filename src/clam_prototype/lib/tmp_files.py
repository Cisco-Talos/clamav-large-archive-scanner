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
        if filetype.get_filetype_short() in path:
            return filetype

    return FileType.UNKNOWN
