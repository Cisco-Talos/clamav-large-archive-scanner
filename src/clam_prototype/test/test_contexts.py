from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

import common

EXPECTED_TMP_DIR_PARENT = '/tmp/some_tmp_dir_for_files_parent'
EXPECTED_TMP_DIR = f'{EXPECTED_TMP_DIR_PARENT}/some_tmp_dir_for_files'
EXPECTED_FILE_PATH = '/some/path/some_archive.tar'

EXPECTED_FILE_META = common.make_file_meta(EXPECTED_FILE_PATH)


@pytest.fixture(scope='session', autouse=True)
def init_logging():
    common.init_logging()


# Mock Fixtures
@pytest.fixture(scope='function')
def mock_tmp_files():
    return MagicMock()


@pytest.fixture(scope='function')
def mock_shutil():
    return MagicMock()


@pytest.fixture(scope='function', autouse=True)
def setup_and_teardown(mocker: MockerFixture, mock_tmp_files, mock_shutil):
    # Before logic
    # These are re-mocked for every single test
    mocker.patch('lib.contexts.tmp_files', mock_tmp_files)
    mocker.patch('lib.contexts.shutil', mock_shutil)

    mock_tmp_files.make_temp_dir.return_value = EXPECTED_TMP_DIR

    yield

    # After logic
    # print('--AFTER--')


def _create_default_u_ctx():
    from lib.contexts import UnpackContext

    return UnpackContext(EXPECTED_FILE_META, EXPECTED_TMP_DIR_PARENT)


def test_unpack_ctx_create_tmp_dir(mock_tmp_files):
    u_ctx = _create_default_u_ctx()

    u_ctx.create_tmp_dir()

    mock_tmp_files.make_temp_dir.assert_called_once_with(EXPECTED_FILE_META, EXPECTED_TMP_DIR_PARENT)


def test_unpack_ctx_cleanup_tmp(mock_shutil):
    u_ctx = _create_default_u_ctx()

    u_ctx.create_tmp_dir()

    u_ctx.cleanup_tmp()

    mock_shutil.rmtree.assert_called_once_with(EXPECTED_TMP_DIR, ignore_errors=True)


def test_unpack_ctx_cleanup_tmp_no_create(mock_shutil):
    u_ctx = _create_default_u_ctx()

    u_ctx.cleanup_tmp()

    mock_shutil.rmtree.assert_not_called()


def test_unpack_ctx_strip_tmp():
    u_ctx = _create_default_u_ctx()
    u_ctx.create_tmp_dir()

    assert u_ctx._strip_tmp(u_ctx, f'{EXPECTED_TMP_DIR}/some_file') == '/some_file'


def test_unpack_ctx_strip_tmp_no_unpack_dir():
    u_ctx = _create_default_u_ctx()

    assert u_ctx._strip_tmp(u_ctx, f'{EXPECTED_TMP_DIR}/some_file') == f'{EXPECTED_TMP_DIR}/some_file'


def test_unpack_ctx_nice_filename_no_parent():
    u_ctx = _create_default_u_ctx()

    assert u_ctx.nice_filename() == EXPECTED_FILE_META.get_filename()


def test_unpack_ctx_nice_filename_with_parent():
    u_ctx = _create_default_u_ctx()
    u_ctx.parent_ctx = _create_default_u_ctx()

    assert u_ctx.nice_filename() == f'{EXPECTED_FILE_META.get_filename()}::{EXPECTED_FILE_PATH}'


def test_unpack_ctx_str_no_unpack_dir():
    u_ctx = _create_default_u_ctx()

    assert str(u_ctx) == f'{EXPECTED_FILE_META.get_filename()} -> Not unpacked'


def test_unpack_ctx_str():
    u_ctx = _create_default_u_ctx()
    u_ctx.create_tmp_dir()

    assert str(u_ctx) == f'{EXPECTED_FILE_META.get_filename()} -> {EXPECTED_TMP_DIR}'


def test_unpack_ctx_detmp_filepath_no_unpack_dir():
    u_ctx = _create_default_u_ctx()

    expected_message = f'{EXPECTED_TMP_DIR}/some_file'

    assert u_ctx.detmp_filepath(expected_message) == expected_message


def test_unpack_ctx_detmp():
    u_ctx = _create_default_u_ctx()
    u_ctx.create_tmp_dir()

    expected_message = f'{EXPECTED_TMP_DIR}/some_file'

    expected_nice_filename = f'{EXPECTED_FILE_META.get_filename()}/some_file'

    assert u_ctx.detmp_filepath(expected_message) == expected_nice_filename
