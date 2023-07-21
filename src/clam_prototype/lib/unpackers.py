import shutil
import tempfile

import lib.detect as detect

HANDLED_FILETYPES = [
    detect.FileType.ISO,
    detect.FileType.TAR,
    detect.FileType.VMDK,
    detect.FileType.ZIP
]


def _make_temp_dir():
    return tempfile.mkdtemp(prefix='clam_unpacker_', dir='/tmp')


def _clean_temp_dir(temp_dir: str):
    shutil.rmtree(path=temp_dir, ignore_errors=True)


def _unpack_iso(filepath: str, work_dir: str) -> str:
    pass


def _unpack_tar(filepath: str, work_dir: str) -> None:
    shutil.unpack_archive(filepath, work_dir, format='tar')


def _unpack_vmdk(filepath: str, work_dir: str) -> str:
    pass


def _unpack_zip(filepath: str, work_dir: str) -> None:
    shutil.unpack_archive(filepath, work_dir, format='zip')


def _is_handled_filetype(type: detect.FileType) -> bool:
    return type in HANDLED_FILETYPES


def _do_unpack(file: detect.FileMetadata) -> str:
    # Make a temp dir to work with
    if _is_handled_filetype(file.filetype):
        dest_dir = _make_temp_dir()
    else:
        raise RuntimeError(f'Unhandled file type: {file.filetype}')

    if file.filetype == detect.FileType.ISO:
        _unpack_iso(file.path, dest_dir)
    elif file.filetype == detect.FileType.TAR:
        _unpack_tar(file.path, dest_dir)
    elif file.filetype == detect.FileType.VMDK:
        _unpack_vmdk(file.path, dest_dir)
    elif file.filetype == detect.FileType.ZIP:
        _unpack_zip(file.path, dest_dir)

    return dest_dir


def unpack(file: detect.FileMetadata) -> list[str]:
    temp_dir = _do_unpack(file)
    pass
