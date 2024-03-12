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

# A wrapper around calling clamdscan with a bit of validation thrown in

import subprocess

from clamav_large_archive_scanner.lib import fast_log
from clamav_large_archive_scanner.lib.contexts import UnpackContext


def validate_clamdscan() -> bool:
    """
    :return: True if clamdscan is available, False otherwise
    """

    result = subprocess.run(['which', 'clamdscan'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if result.returncode != 0:
        return False

    return True


def _run_clamdscan(path: str, all_match: bool) -> (bool, str):
    """
    :param path: A path to scan
    :param all_match: If true, will pass in --allmatch to clam
    :return: True if no malware is found, False otherwise
    """

    clam_args = ['clamdscan', '-m', '--stdout']
    if all_match:
        clam_args.append('--allmatch')

    clam_args.append(path)

    result = subprocess.run(clam_args, capture_output=True, text=True)

    if result.returncode != 0:
        return False, result.stdout

    return True, ""


def clamdscan(u_ctxs: list[UnpackContext], fail_fast: bool, all_match: bool) -> bool:
    """
    :param u_ctxs: A list of UnpackContexts, containing the paths to scan
    :param fail_fast: If true, will stop scanning after the first failure in the list of paths.
    :param all_match: If true, will pass in --allmatch to clam, which will return all malware found
    :return: True if no malware is found, False otherwise
    """

    paths_clean = True

    for a_ctx in u_ctxs:
        fast_log.info(f'Scanning {a_ctx.nice_filename()}')
        is_clean, clamdscan_output = _run_clamdscan(a_ctx.unpacked_dir_location, all_match)
        if not is_clean:
            paths_clean = False
            fast_log.warn('!' * 80)
            fast_log.warn(f'Malware found by clamdscan in file {a_ctx.nice_filename()}:')
            fast_log.warn(a_ctx.detmp_filepath(clamdscan_output))
            fast_log.warn('!' * 80)
            if fail_fast:
                return False

    if paths_clean:
        fast_log.info('=' * 80)
        fast_log.info('No malware found by clamdscan, all clear!')
        fast_log.info('=' * 80)

    return paths_clean
