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

# A wrapper around calling clamdscan with a bit of validation thrown in

import subprocess

from lib import fast_log
from lib.contexts import UnpackContext


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
    :return: True if no virus is found, False otherwise
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
    :param all_match: If true, will pass in --allmatch to clam, which will return all viruses found
    :return: True if no virus is found, False otherwise
    """

    paths_clean = True

    for a_ctx in u_ctxs:
        fast_log.info(f'Scanning {a_ctx.nice_filename()}')
        is_clean, clamdscan_output = _run_clamdscan(a_ctx.unpacked_dir_location, all_match)
        if not is_clean:
            paths_clean = False
            fast_log.error('!' * 80)
            fast_log.error(f'Viruses found by clamdscan in file {a_ctx.nice_filename()}:')
            fast_log.error(a_ctx.detmp_filepath(clamdscan_output))
            fast_log.error('!' * 80)
            if fail_fast:
                return False

    if paths_clean:
        fast_log.info('=' * 80)
        fast_log.info('No viruses found by clamdscan, all clear!')
        fast_log.info('=' * 80)

    return paths_clean
