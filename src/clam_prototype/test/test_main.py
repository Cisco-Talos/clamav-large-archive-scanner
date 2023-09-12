import subprocess
from unittest.mock import MagicMock
from click.testing import CliRunner

import click
import pytest
from pytest_mock import MockerFixture

from lib.file_data import FileMetadata, FileType

EXPECTED_PATH = '/some/path/some_archive.tar'
EXPECTED_MIN_SIZE = '100M'
EXPECTED_MIN_SIZE_BYTES = 100 * 1024 * 1024
EXPECTED_TMP_DIR = '/tmp'
EXPECTED_UNPACKED_DIRS = ['/tmp/some_dir_1', '/tmp/some_dir_2', '/tmp/some_dir_3']
EXPECTED_UNPACKED_DIR = '/tmp/some_dir_4'


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
    mocker.patch('main.cleaner', mock_cleaner)
    mocker.patch('main.detect', mock_detect)
    mocker.patch('main.unpacker', mock_unpacker)
    mocker.patch('main.scanner', mock_scanner)

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


def _set_clamdscan_clean(mock_scanner, is_clean: bool):
    mock_scanner.clamdscan.return_value = is_clean


def _assert_unpack_logic(mock_detect, mock_unpacker, expected_path, expected_recursive, expected_min_size_bytes,
                         expected_tmp_dir, expected_file_meta):
    mock_detect.file_meta_from_path.assert_called_once_with(expected_path)
    if expected_recursive:
        mock_unpacker.unpack_recursive.assert_called_once_with(expected_file_meta, expected_min_size_bytes,
                                                               expected_tmp_dir)
    else:
        mock_unpacker.unpack.assert_called_once_with(expected_file_meta, expected_tmp_dir)


def test_deepscan_no_clamdscan(mock_scanner):
    from main import _deepscan
    _set_clamdscan_present(mock_scanner, False)

    with pytest.raises(click.ClickException) as e:
        _deepscan(EXPECTED_PATH, EXPECTED_MIN_SIZE, False, False, EXPECTED_TMP_DIR)

    mock_scanner.validate_clamdscan.assert_called_once_with()


def test_deepscan_happy_path(mock_scanner, mock_cleaner, mock_unpacker, mock_detect, testcase_file_meta):
    from main import _deepscan
    _set_clamdscan_present(mock_scanner, True)
    _set_default_unpack_mocks(mock_unpacker, mock_detect, testcase_file_meta)
    _set_clamdscan_clean(mock_scanner, True)

    _deepscan(EXPECTED_PATH, EXPECTED_MIN_SIZE, False, False, EXPECTED_TMP_DIR)

    _assert_unpack_logic(mock_detect, mock_unpacker, EXPECTED_PATH, True, EXPECTED_MIN_SIZE_BYTES, EXPECTED_TMP_DIR,
                         testcase_file_meta)

    mock_scanner.clamdscan.assert_called_once_with(EXPECTED_UNPACKED_DIRS, False)
    mock_cleaner.cleanup_recursive.assert_called_once_with(EXPECTED_PATH, EXPECTED_TMP_DIR)


def test_deepscan_virus_fail_fast(mock_scanner, mock_cleaner, mock_unpacker, mock_detect, testcase_file_meta):
    from main import _deepscan
    _set_clamdscan_present(mock_scanner, True)
    _set_default_unpack_mocks(mock_unpacker, mock_detect, testcase_file_meta)
    _set_clamdscan_clean(mock_scanner, False)

    with pytest.raises(click.ClickException) as e:
        _deepscan(EXPECTED_PATH, EXPECTED_MIN_SIZE, False, True, EXPECTED_TMP_DIR)

    _assert_unpack_logic(mock_detect, mock_unpacker, EXPECTED_PATH, True, EXPECTED_MIN_SIZE_BYTES, EXPECTED_TMP_DIR,
                         testcase_file_meta)

    mock_scanner.clamdscan.assert_called_once_with(EXPECTED_UNPACKED_DIRS, True)
    mock_cleaner.cleanup_recursive.assert_called_once_with(EXPECTED_PATH, EXPECTED_TMP_DIR)


def test_unpack_non_recursive(mock_unpacker, mock_detect, testcase_file_meta):
    from main import _unpack
    _set_default_unpack_mocks(mock_unpacker, mock_detect, testcase_file_meta)

    _unpack(EXPECTED_PATH, False, EXPECTED_MIN_SIZE, False, EXPECTED_TMP_DIR)

    _assert_unpack_logic(mock_detect, mock_unpacker, EXPECTED_PATH, False, EXPECTED_MIN_SIZE_BYTES, EXPECTED_TMP_DIR,
                         testcase_file_meta)

