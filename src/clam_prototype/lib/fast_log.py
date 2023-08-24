import os
from pathlib import Path

from fastlogging import LogInit

LOG_FILE = '/tmp/clam_unpacker.log'

_logger = None


def log_start(log_file_path: str = LOG_FILE):
    global _logger

    if not log_file_path:
        log_file_path = LOG_FILE

    # Delete the log file
    Path(log_file_path).unlink(missing_ok=True)

    _logger = LogInit(pathName=log_file_path, console=False, colors=True)


def fast_log(msg: str):
    global _logger
    if not _logger:
        return
    _logger.info(msg)


def disable_logging():
    global _logger
    _logger = None
