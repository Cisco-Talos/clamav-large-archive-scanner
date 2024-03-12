# Copyright (C) 2023-2024 Cisco Systems, Inc. and/or its affiliates. All rights reserved.
#
# Authors: Dave Zhu (yanbzhu@cisco.com)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of mosquitto nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

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
