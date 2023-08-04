import os
from pathlib import Path

from fastlogging import LogInit

LOG_FILE = '/tmp/clam_unpacker.log'

_logger = None


def log_start():
    global _logger
    # Delete the log file
    Path(LOG_FILE).unlink(missing_ok=True)

    _logger = LogInit(pathName=LOG_FILE, console=False, colors=True)


def fast_log(msg: str):
    global _logger
    if not _logger:
        return
    _logger.info(msg)


def disable_logging():
    global _logger
    _logger = None
