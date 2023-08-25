class MountException(BaseException):
    pass


class ArchiveException(Exception):
    tmp_path = ""
