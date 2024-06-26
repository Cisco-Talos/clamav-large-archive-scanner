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
from typing import List
from unittest.mock import MagicMock

import click
# noinspection PyPackageRequirements
import pytest
from pytest_mock import MockerFixture

import common
from clamav_large_archive_scanner.lib.file_data import FileMetadata, FileType
from clamav_large_archive_scanner.lib.scanner import ScanResult

EXPECTED_PATH = '/some/path/some_archive.tar'
EXPECTED_MIN_SIZE = '100M'
EXPECTED_MIN_SIZE_BYTES = 100 * 1024 * 1024
EXPECTED_TMP_DIR = '/tmp'
EXPECTED_UNPACKED_DIRS = ['/tmp/some_dir_1', '/tmp/some_dir_2', '/tmp/some_dir_3']
EXPECTED_UNPACKED_DIR = '/tmp/some_dir_4'

GOOD_SCAN_RESULT = ScanResult(EXPECTED_PATH, 0)
VIRUS_SCAN_RESULT = ScanResult(EXPECTED_PATH, 1)
ERROR_SCAN_RESULT = ScanResult(EXPECTED_PATH, 2)


@pytest.fixture(scope='session', autouse=True)
def init_logging():
    common.init_logging()


@pytest.fixture(scope='function')
def mock_cleaner():
    return MagicMock()


@pytest.fixture(scope='function')
def mock_detect():
    return MagicMock()


@pytest.fixture(scope='function')
def mock_unpacker():
    return MagicMock()


@pytest.fixture(scope='function')
def mock_scanner():
    return MagicMock()


@pytest.fixture(scope='function')
def testcase_file_meta() -> FileMetadata:
    file_meta = FileMetadata()
    file_meta.filetype = FileType.TAR
    file_meta.path = EXPECTED_PATH
    file_meta.size_raw = 2 * EXPECTED_MIN_SIZE_BYTES
    return file_meta


@pytest.fixture(scope='function', autouse=True)
def setup_and_teardown(mocker: MockerFixture, mock_cleaner, mock_detect, mock_unpacker, mock_scanner):
    # Before logic
    # These are re-mocked for every single test
    mocker.patch('clamav_large_archive_scanner.main.cleaner', mock_cleaner)
    mocker.patch('clamav_large_archive_scanner.main.detect', mock_detect)
    mocker.patch('clamav_large_archive_scanner.main.unpacker', mock_unpacker)
    mocker.patch('clamav_large_archive_scanner.main.scanner', mock_scanner)

    yield
    # After logic
    # print('--AFTER--')
    pass


def _set_detect_file_meta_from_path(mock_detect, file_meta: FileMetadata):
    mock_detect.file_meta_from_path.return_value = file_meta


def _set_clamdscan_present(mock_scanner, clamd_present: bool):
    mock_scanner.validate_clamdscan.return_value = clamd_present


def _set_unpack_recursive(mock_unpacker, unpack_dir: str, unpack_dirs: list):
    mock_unpacker.unpack_recursive.return_value = unpack_dirs
    mock_unpacker.unpack.return_value = unpack_dir


def _set_default_unpack_mocks(mock_unpacker, mock_detect, testcase_file_meta):
    _set_unpack_recursive(mock_unpacker, EXPECTED_UNPACKED_DIR, EXPECTED_UNPACKED_DIRS)
    _set_detect_file_meta_from_path(mock_detect, testcase_file_meta)


def _set_clamdscan_rv(mock_scanner, results: List[ScanResult]):
    mock_scanner.clamdscan.return_value = results


def _assert_unpack_logic(mock_detect, mock_unpacker, expected_path, expected_recursive, expected_min_size_bytes,
                         expected_tmp_dir, expected_file_meta):
    mock_detect.file_meta_from_path.assert_called_once_with(expected_path)
    if expected_recursive:
        mock_unpacker.unpack_recursive.assert_called_once_with(expected_file_meta, expected_min_size_bytes,
                                                               expected_tmp_dir)
    else:
        mock_unpacker.unpack.assert_called_once_with(expected_file_meta, expected_tmp_dir)


def _assert_no_unpack(mock_detect: MagicMock, mock_unpacker: MagicMock):
    mock_detect.assert_not_called()
    mock_unpacker.assert_not_called()


def _assert_no_scan(mock_scanner: MagicMock):
    mock_scanner.assert_not_called()


def _assert_no_cleanup(mock_cleaner: MagicMock):
    mock_cleaner.assert_not_called()


def test_scan_no_clamdscan(mock_scanner):
    from clamav_large_archive_scanner.main import _scan
    _set_clamdscan_present(mock_scanner, False)

    with pytest.raises(click.ClickException) as e:
        _scan(EXPECTED_PATH, EXPECTED_MIN_SIZE, False, False, False, EXPECTED_TMP_DIR)

    mock_scanner.validate_clamdscan.assert_called_once_with()


def test_scan_happy_path(mock_scanner, mock_cleaner, mock_unpacker, mock_detect, testcase_file_meta):
    from clamav_large_archive_scanner.main import _scan
    _set_clamdscan_present(mock_scanner, True)
    _set_default_unpack_mocks(mock_unpacker, mock_detect, testcase_file_meta)
    scan_results = [GOOD_SCAN_RESULT]
    _set_clamdscan_rv(mock_scanner, scan_results)

    scan_rv = _scan(EXPECTED_PATH, EXPECTED_MIN_SIZE, False, False, False, EXPECTED_TMP_DIR)
    assert scan_rv == 0

    _assert_unpack_logic(mock_detect, mock_unpacker, EXPECTED_PATH, True, EXPECTED_MIN_SIZE_BYTES, EXPECTED_TMP_DIR,
                         testcase_file_meta)

    mock_scanner.clamdscan.assert_called_once_with(EXPECTED_UNPACKED_DIRS, False, False)
    mock_cleaner.cleanup_recursive.assert_called_once_with(EXPECTED_PATH, EXPECTED_TMP_DIR)


def test_scan_happy_path_all_match(mock_scanner, mock_cleaner, mock_unpacker, mock_detect, testcase_file_meta):
    from clamav_large_archive_scanner.main import _scan
    _set_clamdscan_present(mock_scanner, True)
    _set_default_unpack_mocks(mock_unpacker, mock_detect, testcase_file_meta)
    scan_results = [GOOD_SCAN_RESULT]
    _set_clamdscan_rv(mock_scanner, scan_results)

    scan_rv = _scan(EXPECTED_PATH, EXPECTED_MIN_SIZE, False, False, True, EXPECTED_TMP_DIR)
    assert scan_rv == 0

    _assert_unpack_logic(mock_detect, mock_unpacker, EXPECTED_PATH, True, EXPECTED_MIN_SIZE_BYTES, EXPECTED_TMP_DIR,
                         testcase_file_meta)

    mock_scanner.clamdscan.assert_called_once_with(EXPECTED_UNPACKED_DIRS, False, True)
    mock_cleaner.cleanup_recursive.assert_called_once_with(EXPECTED_PATH, EXPECTED_TMP_DIR)


def test_scan_virus_fail_fast(mock_scanner, mock_cleaner, mock_unpacker, mock_detect, testcase_file_meta):
    from clamav_large_archive_scanner.main import _scan
    _set_clamdscan_present(mock_scanner, True)
    _set_default_unpack_mocks(mock_unpacker, mock_detect, testcase_file_meta)
    scan_results = [GOOD_SCAN_RESULT, VIRUS_SCAN_RESULT]
    _set_clamdscan_rv(mock_scanner, scan_results)

    scan_rv = _scan(EXPECTED_PATH, EXPECTED_MIN_SIZE, False, True, False, EXPECTED_TMP_DIR)
    assert scan_rv == 1

    _assert_unpack_logic(mock_detect, mock_unpacker, EXPECTED_PATH, True, EXPECTED_MIN_SIZE_BYTES, EXPECTED_TMP_DIR,
                         testcase_file_meta)

    mock_scanner.clamdscan.assert_called_once_with(EXPECTED_UNPACKED_DIRS, True, False)
    mock_cleaner.cleanup_recursive.assert_called_once_with(EXPECTED_PATH, EXPECTED_TMP_DIR)


def test_scan_rv_iterations(mock_scanner, mock_cleaner, mock_unpacker, mock_detect, testcase_file_meta):
    from clamav_large_archive_scanner.main import _scan
    _set_clamdscan_present(mock_scanner, True)
    _set_default_unpack_mocks(mock_unpacker, mock_detect, testcase_file_meta)

    # Good, Virus, Error -> Virus
    scan_results = [GOOD_SCAN_RESULT, VIRUS_SCAN_RESULT, ERROR_SCAN_RESULT]
    _set_clamdscan_rv(mock_scanner, scan_results)

    scan_rv = _scan(EXPECTED_PATH, EXPECTED_MIN_SIZE, False, False, False, EXPECTED_TMP_DIR)
    assert scan_rv == 1

    # Good, Error -> Error
    scan_results = [GOOD_SCAN_RESULT, ERROR_SCAN_RESULT]
    _set_clamdscan_rv(mock_scanner, scan_results)

    scan_rv = _scan(EXPECTED_PATH, EXPECTED_MIN_SIZE, False, False, False, EXPECTED_TMP_DIR)
    assert scan_rv == 2


def test_scan_error_all_match_and_ff(mock_scanner, mock_cleaner, mock_unpacker, mock_detect, testcase_file_meta):
    from clamav_large_archive_scanner.main import _scan
    _set_clamdscan_present(mock_scanner, True)

    with pytest.raises(click.ClickException) as e:
        _scan(EXPECTED_PATH, EXPECTED_MIN_SIZE, False, True, True, EXPECTED_TMP_DIR)

    assert e.value.message == 'Cannot specify both --allmatch and --fail-fast'

    _assert_no_unpack(mock_detect, mock_unpacker)
    _assert_no_scan(mock_scanner)
    _assert_no_cleanup(mock_cleaner)


def test_deepscan_no_unpack(mock_scanner, mock_cleaner, mock_unpacker, mock_detect, testcase_file_meta):
    from clamav_large_archive_scanner.main import _scan
    _set_clamdscan_present(mock_scanner, True)
    too_small_meta = testcase_file_meta
    too_small_meta.size_raw = 0
    _set_detect_file_meta_from_path(mock_detect, too_small_meta)

    scan_results = [GOOD_SCAN_RESULT]
    _set_clamdscan_rv(mock_scanner, scan_results)

    _scan(EXPECTED_PATH, EXPECTED_MIN_SIZE, False, False, False, EXPECTED_TMP_DIR)

    _assert_no_unpack(mock_detect, mock_unpacker)
    mock_scanner.clamdscan.assert_called_once()
    _assert_no_cleanup(mock_cleaner)

    scanner_call_ctxs = mock_scanner.clamdscan.call_args[0][0]
    assert len(scanner_call_ctxs) == 1
    assert scanner_call_ctxs[0].unpacked_dir_location == EXPECTED_PATH



def test_unpack_non_recursive(mock_unpacker, mock_detect, testcase_file_meta):
    from clamav_large_archive_scanner.main import _unpack
    _set_default_unpack_mocks(mock_unpacker, mock_detect, testcase_file_meta)

    _unpack(EXPECTED_PATH, False, EXPECTED_MIN_SIZE, False, EXPECTED_TMP_DIR)

    _assert_unpack_logic(mock_detect, mock_unpacker, EXPECTED_PATH, False, EXPECTED_MIN_SIZE_BYTES, EXPECTED_TMP_DIR,
                         testcase_file_meta)
