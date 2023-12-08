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

import subprocess
from unittest.mock import MagicMock

# noinspection PyPackageRequirements
import pytest
from pytest_mock import MockerFixture

import common
from lib.contexts import UnpackContext


@pytest.fixture(scope='session', autouse=True)
def init_logging():
    common.init_logging()


@pytest.fixture(scope='function')
def mock_subprocess():
    return MagicMock()


@pytest.fixture(scope='function', autouse=True)
def setup_and_teardown(mocker: MockerFixture, mock_subprocess):
    # Before logic
    # These are re-mocked for every single test
    mocker.patch('lib.scanner.subprocess', mock_subprocess)

    # Make devnull correct
    mock_subprocess.DEVNULL = subprocess.DEVNULL

    yield
    # After logic
    # print('--AFTER--')
    pass


def _make_subprocess_result(stdout: str, stderr: str, returncode: int):
    result = MagicMock()
    result.stdout = stdout
    result.stderr = stderr
    result.returncode = returncode
    return result


def _assert_which_clamdscan_called(mock_subprocess):
    mock_subprocess.run.assert_called_once_with(['which', 'clamdscan'], stdout=subprocess.DEVNULL,
                                                stderr=subprocess.DEVNULL)


def _assert_run_clamdscan_called(mock_subprocess, u_ctx: UnpackContext, all_match: bool):
    expected_args = ['clamdscan', '-m', '--stdout']
    if all_match:
        expected_args.append('--allmatch')
    expected_args.append(u_ctx.unpacked_dir_location)

    mock_subprocess.run.assert_any_call(expected_args, capture_output=True, text=True)


def test_validate_clamd_present(mock_subprocess):
    from lib.scanner import validate_clamdscan
    mock_subprocess.run.return_value = _make_subprocess_result('', '', 0)

    assert validate_clamdscan()
    _assert_which_clamdscan_called(mock_subprocess)


def test_validate_clamd_not_present(mock_subprocess):
    from lib.scanner import validate_clamdscan
    mock_subprocess.run.return_value = _make_subprocess_result('', '', 1)

    assert not validate_clamdscan()
    _assert_which_clamdscan_called(mock_subprocess)


EXPECTED_CTXS = [
    common.make_basic_unpack_ctx('some_unpack_path_1', 'some_file_path_1'),
    common.make_basic_unpack_ctx('some_unpack_path_2', 'some_file_path_2'),
    common.make_basic_unpack_ctx('some_unpack_path_3', 'some_file_path_3'),
]


def test_clamdscan_clean(mock_subprocess):
    from lib.scanner import clamdscan
    mock_subprocess.run.return_value = _make_subprocess_result('', '', 0)

    assert clamdscan(EXPECTED_CTXS, False, False)

    for ctx in EXPECTED_CTXS:
        _assert_run_clamdscan_called(mock_subprocess, ctx, False)


def test_clamdscan_clean_all_match(mock_subprocess):
    from lib.scanner import clamdscan
    mock_subprocess.run.return_value = _make_subprocess_result('', '', 0)

    assert clamdscan(EXPECTED_CTXS, False, True)

    for ctx in EXPECTED_CTXS:
        _assert_run_clamdscan_called(mock_subprocess, ctx, True)


def test_clamdscan_virus_found(mock_subprocess):
    from lib.scanner import clamdscan
    mock_subprocess.run.return_value = _make_subprocess_result('', '', 1)

    assert not clamdscan(EXPECTED_CTXS, False, False)

    for ctx in EXPECTED_CTXS:
        _assert_run_clamdscan_called(mock_subprocess, ctx, False)


def _fail_second_path_side_effect(*args, **kwargs):
    if args[0][-1] == EXPECTED_CTXS[1].unpacked_dir_location:
        return _make_subprocess_result('', '', 1)
    else:
        return _make_subprocess_result('', '', 0)


def test_clamdsan_virus_found_fail_fast(mock_subprocess):
    from lib.scanner import clamdscan
    mock_subprocess.run.side_effect = _fail_second_path_side_effect

    assert not clamdscan(EXPECTED_CTXS, True, False)

    _assert_run_clamdscan_called(mock_subprocess, EXPECTED_CTXS[0], False)
    _assert_run_clamdscan_called(mock_subprocess, EXPECTED_CTXS[1], False)
    assert mock_subprocess.run.call_count == 2
