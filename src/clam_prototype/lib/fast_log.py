from pathlib import Path

from fastlogging import LogInit, Logger, INFO, DEBUG

LOG_FILE = '/tmp/clam_unpacker.log'

_trace_logger = None  # type: Logger
_console_logger = None  # type: Logger
_log_level = INFO


def log_start(enable_verbose: bool, enable_trace: bool, trace_file_path: str = LOG_FILE):
    global _trace_logger
    global _console_logger
    global _log_level

    if enable_verbose:
        _log_level = DEBUG

    # Fastlogging has a bug with colors, it is global across all loggers, not just the one you're using
    # It's quite dumb
    _console_logger = LogInit(pathName=None, console=True, colors=True, level=_log_level)

    if enable_trace:
        if not trace_file_path:
            trace_file_path = LOG_FILE
        # Delete the log file
        Path(trace_file_path).unlink(missing_ok=True)
        _trace_logger = LogInit(pathName=trace_file_path, console=False, colors=True)
        info(f'Trace logging enabled, logging to {trace_file_path}')


def trace(msg: str):
    global _trace_logger

    if not _trace_logger:
        return

    _trace_logger.debug(msg)


def info(msg: str):
    global _console_logger
    if _console_logger:
        _console_logger.info(msg)


def debug(msg: str):
    global _console_logger
    if _console_logger:
        _console_logger.debug(msg)


def error(msg: str):
    global _console_logger
    if _console_logger:
        _console_logger.error(msg)


def warn(msg: str):
    global _console_logger
    if _console_logger:
        _console_logger.warning(msg)


def disable_logging():
    global _trace_logger
    global _console_logger

    _trace_logger = None
    _console_logger = None
