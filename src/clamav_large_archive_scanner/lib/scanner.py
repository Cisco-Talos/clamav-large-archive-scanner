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
from typing import List, Tuple

from clamav_large_archive_scanner.lib import fast_log
from clamav_large_archive_scanner.lib.contexts import UnpackContext


class ScanResult:
    def __init__(self, path: str, return_code: int):
        self.path = path
        self.clamdscan_rv = return_code

    def _get_scancode_str(self) -> str:
        if self.clamdscan_rv == 0:
            return 'No virus found.'
        elif self.clamdscan_rv == 1:
            return 'Virus(es) found.'
        elif self.clamdscan_rv == 2:
            return 'An error occured.'
        else:
            return 'Unknown return code.'

    def __str__(self):
        return f'{self.path}: {self._get_scancode_str()}'

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.path == other.path and self.clamdscan_rv == other.clamdscan_rv


def validate_clamdscan() -> bool:
    """
    :return: True if clamdscan is available, False otherwise
    """

    result = subprocess.run(['which', 'clamdscan'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if result.returncode != 0:
        return False

    return True


def _run_clamdscan(path: str, all_match: bool) -> Tuple[int, str]:
    """
    :param path: A path to scan
    :param all_match: If true, will pass in --allmatch to clam
    :return: Returns the RV of clamdscan, which as per man page is this:

            Return Codes
                0 : No virus found.
                1 : Virus(es) found.
                2 : An error occured[sic].
    """

    clam_args = ['clamdscan', '-m', '--stdout']
    if all_match:
        clam_args.append('--allmatch')

    clam_args.append(path)

    result = subprocess.run(clam_args, capture_output=True, text=True)
    return result.returncode, result.stdout


def clamdscan(u_ctxs: list[UnpackContext], fail_fast: bool, all_match: bool) -> List[ScanResult]:
    """
    :param u_ctxs: A list of UnpackContexts, containing the paths to scan
    :param fail_fast: If true, will stop scanning after the first failure in the list of paths.
    :param all_match: If true, will pass in --allmatch to clam, which will return all malware found
    :return: A list of tuples containing the path and the return code of clamdscan
    """

    results = []

    for a_ctx in u_ctxs:
        fast_log.info(f'Scanning {a_ctx.nice_filename()}')
        clamdscan_rv, clamdscan_output = _run_clamdscan(a_ctx.unpacked_dir_location, all_match)
        results.append(ScanResult(a_ctx.nice_filename(), clamdscan_rv))
        if clamdscan_rv != 0:
            fast_log.info('!' * 80)
            if clamdscan_rv == 1:
                # Virus Path
                fast_log.warn(f'Malware found by clamdscan in file: {a_ctx.nice_filename()}:')
            elif clamdscan_rv == 2:
                # Clamdscan error Path
                fast_log.info(f'Error in clamdscan when scanning file: {a_ctx.nice_filename()}:')
            fast_log.info(a_ctx.detmp_filepath(clamdscan_output))
            fast_log.info('!' * 80)

            if fail_fast:
                return results

    return results
