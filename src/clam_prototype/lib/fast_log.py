#  Copyright (C) 2023 Cisco Systems, Inc. and/or its affiliates. All rights reserved.
#
#  Authors: Dave Zhu (yanbzhu@cisco.com)
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License version 2 as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

from pathlib import Path

from fastlogging import LogInit, Logger, INFO, DEBUG

LOG_FILE = '/tmp/clam_unpacker.log'

_trace_logger = None  # type: Logger | None
_console_logger = None  # type: Logger | None
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
