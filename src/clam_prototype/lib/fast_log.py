import os

from fastlogging import LogInit

LOG_FILE = '/tmp/clam_unpacker.log'

_logger = None


def log_start():
    global _logger
    # Delete the log file
    os.remove(LOG_FILE)

    _logger = LogInit(pathName=LOG_FILE, console=False, colors=True)


def fast_log(msg: str):
    global _logger
    _logger.info(msg)
    _logger.flush()
