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

import os
from unittest.mock import MagicMock

# noinspection PyPackageRequirements
import pytest
from pytest_mock import MockerFixture

import common
from clamav_large_archive_scanner.lib.file_data import FileMetadata, FileType

EXPECTED_TMP_FILE_PREFIX = 'clam_unpacker'
EXPECTED_TMP_DIR = '/tmp2_just_to_be_different'

EXPECTED_FILE_TYPE = FileType.TAR
EXPECTED_ARCHIVE_NAME = f'some_test_file.{EXPECTED_FILE_TYPE.get_filetype_short()}'
EXPECTED_ARCHIVE_PATH = f'{EXPECTED_TMP_DIR}/{EXPECTED_ARCHIVE_NAME}'
EXPECTED_PARENT_FILE_TYPE = FileType.ISO
EXPECTED_PARENT_NAME = f'some_parent_name.{EXPECTED_PARENT_FILE_TYPE.get_filetype_short()}'
EXPECTED_PARENT_PATH = f'{EXPECTED_TMP_DIR}/{EXPECTED_PARENT_NAME}'

EXPECTED_MKDTEMP_PREFIX_NO_PARENT = f'{EXPECTED_TMP_FILE_PREFIX}_{EXPECTED_FILE_TYPE.get_filetype_short()}_{EXPECTED_ARCHIVE_NAME}_'
EXPECTED_MKDTEMP_PREFIX_WITH_PARENT = f'{EXPECTED_TMP_FILE_PREFIX}_{EXPECTED_FILE_TYPE.get_filetype_short()}-p_{EXPECTED_PARENT_NAME}_p-{EXPECTED_ARCHIVE_NAME}_'

EXPECTED_MKDTEMP_RV = '/tmp/some_temp_dir'  # Doesn't have to be real or match the prefix since mocks


@pytest.fixture(scope='session', autouse=True)
def init_logging():
    common.init_logging()


@pytest.fixture(scope='function')
def mock_glob():
    return MagicMock()


@pytest.fixture(scope='function')
def mock_tempfile():
    return MagicMock()


@pytest.fixture(scope='function')
def mock_os():
    return MagicMock()


@pytest.fixture(scope='function', autouse=True)
def setup_and_teardown(mocker: MockerFixture, mock_glob, mock_tempfile, mock_os):
    # Before logic
    # These are re-mocked for every single test
    mocker.patch('clamav_large_archive_scanner.lib.tmp_files.glob', mock_glob)
    mocker.patch('clamav_large_archive_scanner.lib.tmp_files.tempfile', mock_tempfile)
    mocker.patch('clamav_large_archive_scanner.lib.tmp_files.os', mock_os)

    # Make os.path the real one
    mock_os.path = os.path

    yield
    # After logic
    # print('--AFTER--')
    pass


def _make_file_meta(include_parent: bool) -> FileMetadata:
    file_meta = FileMetadata()
    file_meta.filetype = EXPECTED_FILE_TYPE
    file_meta.path = EXPECTED_ARCHIVE_PATH
    if include_parent:
        file_meta.root_meta = FileMetadata()
        file_meta.root_meta.filetype = EXPECTED_PARENT_FILE_TYPE
        file_meta.root_meta.path = EXPECTED_PARENT_PATH

    return file_meta


def test_make_temp_dir_no_parent(mock_tempfile, mock_os):
    from clamav_large_archive_scanner.lib.tmp_files import make_temp_dir

    mock_tempfile.mkdtemp.return_value = EXPECTED_MKDTEMP_RV

    file_meta = _make_file_meta(False)

    assert make_temp_dir(file_meta, EXPECTED_TMP_DIR) == EXPECTED_MKDTEMP_RV

    mock_tempfile.mkdtemp.assert_called_once_with(prefix=EXPECTED_MKDTEMP_PREFIX_NO_PARENT, dir=EXPECTED_TMP_DIR)
    mock_os.chmod.assert_called_once_with(EXPECTED_MKDTEMP_RV, 0o755)


def test_make_tmp_dir_with_parent(mock_tempfile, mock_os):
    from clamav_large_archive_scanner.lib.tmp_files import make_temp_dir

    mock_tempfile.mkdtemp.return_value = EXPECTED_MKDTEMP_RV

    file_meta = _make_file_meta(True)

    assert make_temp_dir(file_meta, EXPECTED_TMP_DIR) == EXPECTED_MKDTEMP_RV

    mock_tempfile.mkdtemp.assert_called_once_with(prefix=EXPECTED_MKDTEMP_PREFIX_WITH_PARENT, dir=EXPECTED_TMP_DIR)
    mock_os.chmod.assert_called_once_with(EXPECTED_MKDTEMP_RV, 0o755)


HANDLED_FILE_TYPES = [FileType.TAR, FileType.TARGZ, FileType.ZIP, FileType.ISO, FileType.VMDK, FileType.QCOW2]


def test_detect_filetype():
    from clamav_large_archive_scanner.lib.tmp_files import determine_tmp_dir_filetype

    for filetype in HANDLED_FILE_TYPES:
        assert determine_tmp_dir_filetype(f'/tmp/{EXPECTED_TMP_FILE_PREFIX}_{filetype.get_filetype_short()}') == filetype

    # Test that it returns UNKNOWN for a file that doesn't belong to us
    assert determine_tmp_dir_filetype(f'/tmp/someone_elses_file.tar') == FileType.UNKNOWN


def test_find_associated_dirs(mock_glob):
    from clamav_large_archive_scanner.lib.tmp_files import find_associated_dirs

    expected_glob_return = [EXPECTED_ARCHIVE_PATH]

    mock_glob.glob.return_value = expected_glob_return
    assert find_associated_dirs(EXPECTED_ARCHIVE_PATH, EXPECTED_TMP_DIR) == expected_glob_return

    mock_glob.glob.assert_called_once_with(f'{EXPECTED_TMP_DIR}/{EXPECTED_TMP_FILE_PREFIX}_*_{EXPECTED_ARCHIVE_NAME}_*')
