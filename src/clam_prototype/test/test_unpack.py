import os
from unittest.mock import MagicMock, call

import click
# noinspection PyPackageRequirements
import pytest
from pytest_mock import MockerFixture

from lib.exceptions import ArchiveException, MountException
from lib.file_data import FileMetadata, FileType

EXPECTED_TMP_DIR_PARENT = '/tmp/some_tmp_dir_for_files_parent'
EXPECTED_TMP_DIR = f'{EXPECTED_TMP_DIR_PARENT}/some_tmp_dir_for_files'
EXPECTED_ARCHIVE_PATH = '/tmp/some_archive_path.tar'

EXPECTED_TAR_FILE_FORMAT = 'tar'
EXPECTED_ZIP_FILE_FORMAT = 'zip'
EXPECTED_TGZ_FILE_FORMAT = 'gztar'

EXPECTED_GUESTFS_PARTITIONS = ['/dev/sda1', '/dev/sda2', '/dev/sda3']

EXPECTED_HANDLED_FILE_TYPES = [FileType.TAR, FileType.ISO, FileType.VMDK, FileType.ZIP, FileType.TARGZ, FileType.QCOW2,
                               FileType.DIR]


# Mock Fixtures
@pytest.fixture(scope='function')
def mock_tmp_files():
    return MagicMock()


@pytest.fixture(scope='function')
def mock_shutil():
    return MagicMock()


@pytest.fixture(scope='function')
def mock_mount_tools():
    return MagicMock()


@pytest.fixture(scope='function')
def mock_file_data():
    return MagicMock()


@pytest.fixture(scope='function')
def mock_os():
    return MagicMock()


@pytest.fixture(scope='function', autouse=True)
def setup_and_teardown(mocker: MockerFixture, mock_tmp_files, mock_shutil, mock_mount_tools, mock_os, mock_file_data):
    # Before logic
    # These are re-mocked for every single test
    mocker.patch('lib.unpack.tmp_files', mock_tmp_files)
    mocker.patch('lib.unpack.shutil', mock_shutil)
    mocker.patch('lib.unpack.mount_tools', mock_mount_tools)
    mocker.patch('lib.unpack.os', mock_os)
    mocker.patch('lib.unpack.file_data', mock_file_data)

    mock_tmp_files.make_temp_dir.return_value = EXPECTED_TMP_DIR

    yield

    # After logic
    # print('--AFTER--')


def _make_file_meta() -> FileMetadata:
    file_meta = FileMetadata()
    file_meta.filetype = FileType.TAR
    file_meta.path = EXPECTED_ARCHIVE_PATH

    return file_meta


def _assert_base_file_handler_init_behavior(mock_tmp_files, expected_file_meta, expected_tmp_dir):
    mock_tmp_files.make_temp_dir.assert_called_once_with(expected_file_meta, expected_tmp_dir)


def test_base_file_unpacker(mock_tmp_files):
    from lib.unpack import BaseFileUnpackHandler

    expected_file_meta = _make_file_meta()

    unpacker = BaseFileUnpackHandler(expected_file_meta, EXPECTED_TMP_DIR_PARENT)

    _assert_base_file_handler_init_behavior(mock_tmp_files, expected_file_meta, EXPECTED_TMP_DIR_PARENT)

    with pytest.raises(NotImplementedError):
        unpacker.unpack()


def test_archive_file_unpacker(mock_tmp_files, mock_shutil):
    from lib.unpack import ArchiveFileUnpackHandler

    expected_file_meta = _make_file_meta()

    unpacker = ArchiveFileUnpackHandler(expected_file_meta, EXPECTED_TAR_FILE_FORMAT, EXPECTED_TMP_DIR_PARENT)
    _assert_base_file_handler_init_behavior(mock_tmp_files, expected_file_meta, EXPECTED_TMP_DIR_PARENT)

    unpack_dir = unpacker.unpack()

    assert unpack_dir == EXPECTED_TMP_DIR
    mock_shutil.unpack_archive.assert_called_once_with(expected_file_meta.path, EXPECTED_TMP_DIR,
                                                       format=EXPECTED_TAR_FILE_FORMAT)


def test_archive_file_unpacker_unpack_failed(mock_tmp_files, mock_shutil):
    from lib.unpack import ArchiveFileUnpackHandler

    expected_file_meta = _make_file_meta()

    mock_shutil.unpack_archive.side_effect = Exception('some_archive_exception')

    unpacker = ArchiveFileUnpackHandler(expected_file_meta, EXPECTED_TAR_FILE_FORMAT, EXPECTED_TMP_DIR_PARENT)

    with pytest.raises(ArchiveException):
        unpacker.unpack()

    mock_shutil.unpack_archive.assert_called_once_with(expected_file_meta.path, EXPECTED_TMP_DIR,
                                                       format=EXPECTED_TAR_FILE_FORMAT)
    mock_shutil.rmtree.assert_called_once_with(EXPECTED_TMP_DIR, ignore_errors=True)


def test_iso_unpacker(mock_tmp_files, mock_mount_tools):
    from lib.unpack import IsoFileUnpackHandler

    expected_file_meta = _make_file_meta()

    unpacker = IsoFileUnpackHandler(expected_file_meta, EXPECTED_TMP_DIR_PARENT)
    _assert_base_file_handler_init_behavior(mock_tmp_files, expected_file_meta, EXPECTED_TMP_DIR_PARENT)

    unpack_dir = unpacker.unpack()

    assert unpack_dir == EXPECTED_TMP_DIR
    mock_mount_tools.mount_iso.assert_called_once_with(expected_file_meta.path, EXPECTED_TMP_DIR)


def test_iso_unpacker_mount_error(mock_tmp_files, mock_mount_tools):
    from lib.unpack import IsoFileUnpackHandler

    expected_file_meta = _make_file_meta()

    mock_mount_tools.mount_iso.side_effect = MountException('some_mount_exception')

    unpacker = IsoFileUnpackHandler(expected_file_meta, EXPECTED_TMP_DIR_PARENT)

    with pytest.raises(click.FileError) as e:
        unpacker.unpack()

    mock_mount_tools.mount_iso.assert_called_once_with(expected_file_meta.path, EXPECTED_TMP_DIR)

    assert str(e.value) == f'Unable to mount {expected_file_meta.path} to {EXPECTED_TMP_DIR}'


def _archive_children_helper(mock_tmp_files, handler_class, expected_file_format):
    expected_file_meta = _make_file_meta()

    unpacker = handler_class(expected_file_meta, EXPECTED_TMP_DIR_PARENT)
    _assert_base_file_handler_init_behavior(mock_tmp_files, expected_file_meta, EXPECTED_TMP_DIR_PARENT)

    assert unpacker.format == expected_file_format


def test_tar_unpacker(mock_tmp_files):
    from lib.unpack import TarFileUnpackHandler

    _archive_children_helper(mock_tmp_files, TarFileUnpackHandler, EXPECTED_TAR_FILE_FORMAT)


def test_zip_unpacker(mock_tmp_files):
    from lib.unpack import ZipFileUnpackHandler

    _archive_children_helper(mock_tmp_files, ZipFileUnpackHandler, EXPECTED_ZIP_FILE_FORMAT)


def test_targz_unpacker(mock_tmp_files):
    from lib.unpack import TarGzFileUnpackHandler

    _archive_children_helper(mock_tmp_files, TarGzFileUnpackHandler, EXPECTED_TGZ_FILE_FORMAT)


def _mock_enumerate_guestfs_partitions(mock_mount_tools, return_value):
    mock_mount_tools.enumerate_guestfs_partitions.return_value = return_value


def _assert_guestfs_unpack_calls(mock_mount_tools, expected_file_meta, expected_tmp_dir, expected_partitions):
    mock_mount_tools.enumerate_guestfs_partitions.assert_called_once_with(expected_file_meta.path)

    mock_mount_tools.mount_guestfs_partition.has_calls(
        [call(expected_file_meta.path, x, expected_tmp_dir) for x in expected_partitions], any_order=True)


def test_guestfs_unpacker(mock_tmp_files, mock_mount_tools):
    from lib.unpack import GuestFSFileUnpackHandler

    # For test output formatting... don't remove
    print()

    expected_file_meta = _make_file_meta()
    _mock_enumerate_guestfs_partitions(mock_mount_tools, EXPECTED_GUESTFS_PARTITIONS)

    unpacker = GuestFSFileUnpackHandler(expected_file_meta, EXPECTED_TMP_DIR_PARENT)
    _assert_base_file_handler_init_behavior(mock_tmp_files, expected_file_meta, EXPECTED_TMP_DIR_PARENT)

    unpack_dir = unpacker.unpack()

    assert unpack_dir == EXPECTED_TMP_DIR

    _assert_guestfs_unpack_calls(mock_mount_tools, expected_file_meta, EXPECTED_TMP_DIR, EXPECTED_GUESTFS_PARTITIONS)


def test_guestfs_unpacker_enumerate_error(mock_tmp_files, mock_mount_tools):
    from lib.unpack import GuestFSFileUnpackHandler

    # For test output formatting... don't remove
    print()

    expected_file_meta = _make_file_meta()
    mock_mount_tools.enumerate_guestfs_partitions.side_effect = MountException('some_mount_exception')

    unpacker = GuestFSFileUnpackHandler(expected_file_meta, EXPECTED_TMP_DIR_PARENT)
    _assert_base_file_handler_init_behavior(mock_tmp_files, expected_file_meta, EXPECTED_TMP_DIR_PARENT)

    with pytest.raises(click.FileError) as e:
        unpacker.unpack()

    assert str(e.value) == f'Unable to list partitions for {expected_file_meta.path}, aborting unpack'

    mock_mount_tools.enumerate_guestfs_partitions.assert_called_once_with(expected_file_meta.path)
    mock_mount_tools.mount_guestfs_partition.assert_not_called()


def test_guestfs_unpacker_mount_error(mock_tmp_files, mock_mount_tools):
    from lib.unpack import GuestFSFileUnpackHandler

    # For test output formatting... don't remove
    print()

    expected_file_meta = _make_file_meta()
    _mock_enumerate_guestfs_partitions(mock_mount_tools, EXPECTED_GUESTFS_PARTITIONS)
    mock_mount_tools.mount_guestfs_partition.side_effect = MountException('some_mount_exception')

    unpacker = GuestFSFileUnpackHandler(expected_file_meta, EXPECTED_TMP_DIR_PARENT)
    _assert_base_file_handler_init_behavior(mock_tmp_files, expected_file_meta, EXPECTED_TMP_DIR_PARENT)

    # Errors during mount doesn't stop the logic
    unpacker.unpack()

    _assert_guestfs_unpack_calls(mock_mount_tools, expected_file_meta, EXPECTED_TMP_DIR, EXPECTED_GUESTFS_PARTITIONS)


def test_dir_unpacker(mock_tmp_files):
    from lib.unpack import DirFileUnpackHandler

    expected_file_meta = _make_file_meta()

    unpacker = DirFileUnpackHandler(expected_file_meta)
    mock_tmp_files.make_temp_dir.assert_not_called()

    unpack_dir = unpacker.unpack()

    assert unpack_dir == expected_file_meta.path


def test_is_handled_filetype():
    from lib.unpack import is_handled_filetype

    for filetype in EXPECTED_HANDLED_FILE_TYPES:
        assert is_handled_filetype(filetype)

    assert not is_handled_filetype(FileType.DOES_NOT_EXIST)


def test_unpack(mock_tmp_files):
    from lib.unpack import unpack

    expected_file_meta = _make_file_meta()

    unpack_dir = unpack(expected_file_meta, EXPECTED_TMP_DIR_PARENT)

    assert unpack_dir == EXPECTED_TMP_DIR


def test_unpack_unhandled_filetype(mock_tmp_files):
    from lib.unpack import unpack

    expected_file_meta = _make_file_meta()
    expected_file_meta.filetype = FileType.DOES_NOT_EXIST

    with pytest.raises(click.BadParameter) as e:
        unpack(expected_file_meta, EXPECTED_TMP_DIR_PARENT)

    assert str(e.value) == f'Unhandled file type: {FileType.DOES_NOT_EXIST}'


def test_unpack_archive_exception(mock_tmp_files, mock_shutil):
    from lib.unpack import unpack

    expected_archive_exception_str = 'some_archive_exception'

    expected_file_meta = _make_file_meta()

    mock_shutil.unpack_archive.side_effect = Exception(expected_archive_exception_str)

    with pytest.raises(click.FileError) as e:
        unpack(expected_file_meta, EXPECTED_TMP_DIR_PARENT)

    assert str(
        e.value) == f'Unable to unpack {expected_file_meta.path}, got the following error: {expected_archive_exception_str}'


# This next test takes a ton of setup, since we have to mimic an entire directory structure
# With both valid and invalid files
#
# This is the structure that we are trying to recreate with mocks:
# (parent_archive_top_dir)
#     |- valid_archive_1 (will extract to valid_archive_1_dir)
#     |- invalid_file_1
#     |- (subdir_1)
#         |- valid_archive_2 (will extract to valid_archive_2_dir)
#

#
# We expect that recursive unpack will return a list containing:
# [parent_archive_top_dir, valid_archive_1_dir, valid_archive_2_dir]

PARENT_ARCHIVE = '/tmp/parent_archive.tar'
PARENT_ARCHIVE_UNPACK_DIR = '/tmp/parent_archive_top_dir'
VALID_ARCHIVE_1 = f'{PARENT_ARCHIVE_UNPACK_DIR}/valid_archive_1.tar'
VALID_ARCHIVE_1_UNPACK_DIR = f'/tmp/valid_archive_1_dir'

PARENT_ARCHIVE_SUBDIR_1 = f'{PARENT_ARCHIVE_UNPACK_DIR}/subdir_1'
VALID_ARCHIVE_2 = f'{PARENT_ARCHIVE_SUBDIR_1}/valid_archive_2.tar'
VALID_ARCHIVE_2_UNPACK_DIR = f'/tmp/valid_archive_2_dir'

EXPECTED_RECURSIVE_UNPACK_RESULTS = [PARENT_ARCHIVE_UNPACK_DIR, VALID_ARCHIVE_1_UNPACK_DIR, VALID_ARCHIVE_2_UNPACK_DIR]


def _parent_archive_metadata() -> FileMetadata:
    file_meta = FileMetadata()
    file_meta.filetype = FileType.TAR
    file_meta.path = PARENT_ARCHIVE

    return file_meta


def _recursive_unpack_make_temp_dir_side_effect(*args, **kwargs):
    file_meta = args[0]

    if file_meta.path == PARENT_ARCHIVE:
        return PARENT_ARCHIVE_UNPACK_DIR
    elif file_meta.path == VALID_ARCHIVE_1:
        return VALID_ARCHIVE_1_UNPACK_DIR
    elif file_meta.path == VALID_ARCHIVE_2:
        return VALID_ARCHIVE_2_UNPACK_DIR

    raise Exception(f'Unexpected file meta path: {file_meta.path}')


def _recursive_unpack_os_walk_side_effect(*args, **kwargs):
    target_dir = args[0]

    if target_dir == PARENT_ARCHIVE_UNPACK_DIR:
        return [
            (PARENT_ARCHIVE_UNPACK_DIR, [], [VALID_ARCHIVE_1, 'invalid_file_1']),
            (PARENT_ARCHIVE_SUBDIR_1, [], [VALID_ARCHIVE_2])
        ]

    # Not a directory that we are mocking (likely valid_archive_1_dir or valid_archive_2_dir)
    return []


def _recursive_unpack_file_meta_from_path_side_effect(*args, **kwargs):
    file_path = args[0]

    if file_path == VALID_ARCHIVE_1:
        file_meta = FileMetadata()
        file_meta.filetype = FileType.TAR
        file_meta.path = VALID_ARCHIVE_1

    elif file_path == VALID_ARCHIVE_2:
        file_meta = FileMetadata()
        file_meta.filetype = FileType.TAR
        file_meta.path = VALID_ARCHIVE_2

    else:
        file_meta = FileMetadata()
        file_meta.filetype = FileType.UNKNOWN
        file_meta.path = file_path

    return file_meta


def test_unpack_recursive(mock_tmp_files, mock_shutil, mock_os, mock_file_data):
    from lib.unpack import unpack_recursive
    # For test output formatting... don't remove
    print()

    mock_tmp_files.make_temp_dir.side_effect = _recursive_unpack_make_temp_dir_side_effect
    mock_os.walk.side_effect = _recursive_unpack_os_walk_side_effect
    mock_file_data.file_meta_from_path.side_effect = _recursive_unpack_file_meta_from_path_side_effect

    # Use real join
    mock_os.path.join = os.path.join

    parent_archive_meta = _parent_archive_metadata()

    unpack_dirs = unpack_recursive(parent_archive_meta, 0, EXPECTED_TMP_DIR_PARENT)

    assert unpack_dirs == EXPECTED_RECURSIVE_UNPACK_RESULTS
    # There are no call assertions here, since the only way that these two match is if all the
    # mocks got called correctly
