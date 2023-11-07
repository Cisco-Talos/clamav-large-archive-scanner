from lib import fast_log
from lib.contexts import UnpackContext
from lib.file_data import FileMetadata


def init_logging():
    fast_log.log_start(enable_verbose=True, enable_trace=False)


def make_file_meta(path: str) -> FileMetadata:
    meta = FileMetadata()
    meta.path = path

    return meta


def make_basic_unpack_ctx(unpack_dir: str, file_path: str) -> UnpackContext:
    meta = make_file_meta(file_path)
    ctx = UnpackContext(file_meta=meta, enclosing_tmp_dir='/tmp')
    ctx.unpacked_dir_location = unpack_dir

    return ctx
