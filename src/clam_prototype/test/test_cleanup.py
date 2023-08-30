# Setup and Teardown logic for pytest
from unittest.mock import MagicMock, call

import click
# noinspection PyPackageRequirements
import pytest
from pytest_mock import MockerFixture

import lib.cleanup
import lib.mount_tools
import lib.exceptions
from lib.file_data import FileType

# Some constants

EXPECTED_ARCHIVE_PARENT_DIR = '/tmp/some_archive_parent_dir'
EXPECTED_ARCHIVE_PATH = f'{EXPECTED_ARCHIVE_PARENT_DIR}/some_archive_path.some_archive_format'


# Mock Fixtures
@pytest.fixture(scope='function')
def mock_shutil():
    return MagicMock()


@pytest.fixture(scope='function')
def mock_mount_tools():
    return MagicMock()


@pytest.fixture(scope='function')
def mock_tmp_files():
    return MagicMock()


@pytest.fixture(scope='function', autouse=True)
def setup_and_teardown(mocker: MockerFixture, mock_shutil, mock_mount_tools, mock_tmp_files):
    # Before logic
    # These are re-mocked for every single test
    mocker.patch('lib.cleanup.shutil', mock_shutil)
    mocker.patch('lib.cleanup.mount_tools', mock_mount_tools)
    mocker.patch('lib.cleanup.tmp_files', mock_tmp_files)

    yield

    # After logic
    # print('--AFTER--')


def _assert_base_cleanup_behavior(mock_shutil, handler=None, expected_path=EXPECTED_ARCHIVE_PATH):
    if handler:
        handler.cleanup()

    mock_shutil.rmtree.assert_called_once_with(path=expected_path, ignore_errors=True)


def test_base_cleanup_handler(mock_shutil):
    # For test output formatting... don't remove
    print()

    handler = lib.cleanup.BaseCleanupHandler(EXPECTED_ARCHIVE_PATH)
    _assert_base_cleanup_behavior(mock_shutil, handler)


def test_tar_cleanup_handler(mock_shutil):
    # Tar has the same logic as base
    print()

    handler = lib.cleanup.TarCleanupHandler(EXPECTED_ARCHIVE_PATH)
    _assert_base_cleanup_behavior(mock_shutil, handler)


def test_targz_cleanup_handler(mock_shutil):
    # Tar has the same logic as base
    print()

    handler = lib.cleanup.TarGzCleanupHandler(EXPECTED_ARCHIVE_PATH)
    _assert_base_cleanup_behavior(mock_shutil, handler)


def test_zip_cleanup_handler(mock_shutil):
    # Zip has the same logic as base
    print()

    handler = lib.cleanup.ZipCleanupHandler(EXPECTED_ARCHIVE_PATH)
    _assert_base_cleanup_behavior(mock_shutil, handler)


def test_iso_cleanup_handler(mock_shutil, mock_mount_tools):
    # For test output formatting... don't remove
    print()

    handler = lib.cleanup.IsoCleanupHandler(EXPECTED_ARCHIVE_PATH)
    handler.cleanup()

    mock_mount_tools.umount_iso.assert_called_once_with(EXPECTED_ARCHIVE_PATH)
    mock_shutil.rmtree.assert_called_once_with(path=EXPECTED_ARCHIVE_PATH, ignore_errors=True)


def test_iso_cleanup_handler_mount_error(mock_shutil, mock_mount_tools):
    # For test output formatting... don't remove
    print()

    mock_mount_tools.umount_iso.side_effect = lib.exceptions.MountException('some test error')

    handler = lib.cleanup.IsoCleanupHandler(EXPECTED_ARCHIVE_PATH)

    with pytest.raises(click.FileError) as e:
        handler.cleanup()

    assert str(e.value) == f'Unable to un-mount from {EXPECTED_ARCHIVE_PATH}'
    mock_shutil.rmtree.assert_not_called()


GUESTFS_PARTITIONS = ['/tmp/some_test_path/some_partition_1',
                      '/tmp/some_test_path/some_partition_2',
                      '/tmp/some_test_path/some_partition_3']


def _assert_umount_has_calls(mock_umount):
    mock_umount.assert_has_calls([call(x) for x in GUESTFS_PARTITIONS], any_order=True)


def test_guestfs_cleanup_handler(mock_shutil, mock_mount_tools):
    # For test output formatting... don't remove
    print()

    mock_mount_tools.list_top_level_dirs.return_value = GUESTFS_PARTITIONS

    handler = lib.cleanup.GuestFSCleanupHandler(EXPECTED_ARCHIVE_PATH)
    handler.cleanup()

    _assert_umount_has_calls(mock_mount_tools.umount_guestfs_partition)

    mock_shutil.rmtree.assert_called_once_with(path=EXPECTED_ARCHIVE_PATH, ignore_errors=True)


# Raises an exception on the second partition
def _umount_exception_thrower(dir_name: str):
    if dir_name == GUESTFS_PARTITIONS[1]:
        raise lib.exceptions.MountException('some test error')


def test_guestfs_cleanup_handler_umount_error(mock_shutil, mock_mount_tools):
    # For test output formatting... don't remove
    print()

    mock_mount_tools.list_top_level_dirs.return_value = GUESTFS_PARTITIONS
    mock_mount_tools.umount_guestfs_partition.side_effect = _umount_exception_thrower

    handler = lib.cleanup.GuestFSCleanupHandler(EXPECTED_ARCHIVE_PATH)
    handler.cleanup()

    _assert_umount_has_calls(mock_mount_tools.umount_guestfs_partition)

    # Even in case of errors, it should still continue
    mock_shutil.rmtree.assert_not_called()


ASSOCIATED_DIRS = ['/tmp/ut_a_dir_1', '/tmp/ut_a_dir_2', '/tmp/ut_a_dir_3']


def test_cleanup_path(mock_tmp_files, mock_shutil):
    # For test output formatting... don't remove
    print()

    mock_tmp_files.determine_filetype.return_value = FileType.TAR

    lib.cleanup.cleanup_path(EXPECTED_ARCHIVE_PATH)

    _assert_base_cleanup_behavior(mock_shutil)


def test_cleanup_path_unknown_type(mock_tmp_files, mock_shutil):
    # For test output formatting... don't remove
    print()

    mock_tmp_files.determine_filetype.return_value = FileType.UNKNOWN

    with pytest.raises(click.BadParameter) as e:
        lib.cleanup.cleanup_path(EXPECTED_ARCHIVE_PATH)

    assert str(e.value) == f'Unhandled file type: {FileType.UNKNOWN}'

    mock_shutil.rmtree.assert_not_called()


def test_cleanup_single_file(mock_tmp_files, mock_shutil):
    # For test output formatting... don't remove
    print()

    mock_tmp_files.determine_filetype.return_value = FileType.TAR
    mock_tmp_files.find_associated_dirs.return_value = ASSOCIATED_DIRS

    lib.cleanup.cleanup_file(EXPECTED_ARCHIVE_PATH, EXPECTED_ARCHIVE_PARENT_DIR)

    mock_tmp_files.find_associated_dirs.assert_called_once_with(EXPECTED_ARCHIVE_PATH, EXPECTED_ARCHIVE_PARENT_DIR)
    _assert_base_cleanup_behavior(mock_shutil, expected_path=ASSOCIATED_DIRS[0])


def test_cleanup_recursive(mock_tmp_files, mock_shutil):
    # For test output formatting... don't remove
    print()

    mock_tmp_files.determine_filetype.return_value = FileType.TAR
    mock_tmp_files.find_associated_dirs.return_value = ASSOCIATED_DIRS

    lib.cleanup.cleanup_recursive(EXPECTED_ARCHIVE_PATH, EXPECTED_ARCHIVE_PARENT_DIR)

    mock_tmp_files.find_associated_dirs.assert_called_once_with(EXPECTED_ARCHIVE_PATH, EXPECTED_ARCHIVE_PARENT_DIR)
    mock_shutil.rmtree.assert_has_calls([call(path=x, ignore_errors=True) for x in ASSOCIATED_DIRS], any_order=True)


def test_cleanup_no_files(mock_tmp_files, mock_shutil):
    # For test output formatting... don't remove
    print()

    mock_tmp_files.find_associated_dirs.return_value = []

    lib.cleanup.cleanup_recursive(EXPECTED_ARCHIVE_PATH, EXPECTED_ARCHIVE_PARENT_DIR)

    mock_shutil.assert_not_called()


def test_filetype_handlers():
    # I hate how this looks, but it's the best way to test this...
    # The dictionary is so very important and core to the logic,
    # but otherwise is just a lookup table
    #
    # This testcase is basically a speedbump
    expected_filetype_handlers = {
        FileType.TAR: lib.cleanup.TarCleanupHandler,
        FileType.ZIP: lib.cleanup.ZipCleanupHandler,
        FileType.ISO: lib.cleanup.IsoCleanupHandler,
        FileType.VMDK: lib.cleanup.GuestFSCleanupHandler,
        FileType.TARGZ: lib.cleanup.TarGzCleanupHandler,
        FileType.QCOW2: lib.cleanup.GuestFSCleanupHandler,
    }

    assert lib.cleanup.FILETYPE_HANDLERS == expected_filetype_handlers
