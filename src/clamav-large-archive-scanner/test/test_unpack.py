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

import os
from unittest.mock import MagicMock, call

import click
# noinspection PyPackageRequirements
import pytest
from pytest_mock import MockerFixture

import common
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


@pytest.fixture(scope='session', autouse=True)
def init_logging():
    common.init_logging()


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
def mock_contexts():
    return MagicMock()


@pytest.fixture(scope='function')
def mock_os():
    return MagicMock()


@pytest.fixture(scope='function', autouse=True)
def setup_and_teardown(mocker: MockerFixture, mock_mount_tools, mock_os, mock_file_data, mock_shutil, mock_contexts):
    # Before logic
    # These are re-mocked for every single test
    mocker.patch('lib.unpack.shutil', mock_shutil)
    mocker.patch('lib.unpack.mount_tools', mock_mount_tools)
    mocker.patch('lib.unpack.os', mock_os)
    mocker.patch('lib.unpack.file_data', mock_file_data)
    mocker.patch('lib.unpack.contexts', mock_contexts)

    yield

    # After logic
    # print('--AFTER--')


def _make_file_meta() -> FileMetadata:
    file_meta = FileMetadata()
    file_meta.filetype = FileType.TAR
    file_meta.path = EXPECTED_ARCHIVE_PATH

    return file_meta


def _make_mock_u_ctx() -> MagicMock:
    expected_meta = _make_file_meta()
    expected_ctx = MagicMock()
    expected_ctx.file_meta = expected_meta
    expected_ctx.unpacked_dir_location = EXPECTED_TMP_DIR

    return expected_ctx


def _assert_base_file_handler_init_behavior(mock_u_ctx: MagicMock):
    mock_u_ctx.create_tmp_dir.assert_called_once()


def test_base_file_unpacker():
    from lib.unpack import BaseFileUnpackHandler

    mock_u_ctx = _make_mock_u_ctx()

    unpacker = BaseFileUnpackHandler(mock_u_ctx)

    _assert_base_file_handler_init_behavior(mock_u_ctx)

    with pytest.raises(NotImplementedError):
        unpacker.unpack()


def test_archive_file_unpacker(mock_shutil):
    from lib.unpack import ArchiveFileUnpackHandler

    mock_u_ctx = _make_mock_u_ctx()

    unpacker = ArchiveFileUnpackHandler(mock_u_ctx, EXPECTED_TAR_FILE_FORMAT)
    _assert_base_file_handler_init_behavior(mock_u_ctx)

    unpack_ctx = unpacker.unpack()

    assert unpack_ctx == mock_u_ctx
    mock_shutil.unpack_archive.assert_called_once_with(EXPECTED_ARCHIVE_PATH, EXPECTED_TMP_DIR,
                                                       format=EXPECTED_TAR_FILE_FORMAT)


def test_archive_file_unpacker_unpack_failed(mock_shutil):
    from lib.unpack import ArchiveFileUnpackHandler

    mock_u_ctx = _make_mock_u_ctx()

    mock_shutil.unpack_archive.side_effect = Exception('some_archive_exception')

    unpacker = ArchiveFileUnpackHandler(mock_u_ctx, EXPECTED_TAR_FILE_FORMAT)

    with pytest.raises(ArchiveException):
        unpacker.unpack()

    mock_shutil.unpack_archive.assert_called_once_with(EXPECTED_ARCHIVE_PATH, EXPECTED_TMP_DIR,
                                                       format=EXPECTED_TAR_FILE_FORMAT)
    mock_u_ctx.cleanup_tmp.assert_called_once()


def test_iso_unpacker(mock_mount_tools):
    from lib.unpack import IsoFileUnpackHandler

    mock_u_ctx = _make_mock_u_ctx()

    unpacker = IsoFileUnpackHandler(mock_u_ctx)
    _assert_base_file_handler_init_behavior(mock_u_ctx)

    unpack_ctx = unpacker.unpack()

    assert unpack_ctx == mock_u_ctx
    mock_mount_tools.mount_iso.assert_called_once_with(EXPECTED_ARCHIVE_PATH, EXPECTED_TMP_DIR)


def test_iso_unpacker_mount_error(mock_mount_tools):
    from lib.unpack import IsoFileUnpackHandler

    mock_u_ctx = _make_mock_u_ctx()

    mock_mount_tools.mount_iso.side_effect = MountException('some_mount_exception')

    unpacker = IsoFileUnpackHandler(mock_u_ctx)

    with pytest.raises(click.FileError) as e:
        unpacker.unpack()

    mock_mount_tools.mount_iso.assert_called_once_with(EXPECTED_ARCHIVE_PATH, EXPECTED_TMP_DIR)

    assert str(e.value) == f'Unable to mount {EXPECTED_ARCHIVE_PATH} to {EXPECTED_TMP_DIR}'


def _archive_unpacker_children_test_and_assert(handler_class, expected_file_format):
    mock_u_ctx = _make_mock_u_ctx()

    unpacker = handler_class(mock_u_ctx)
    _assert_base_file_handler_init_behavior(mock_u_ctx)

    assert unpacker.format == expected_file_format


def test_tar_unpacker():
    from lib.unpack import TarFileUnpackHandler

    _archive_unpacker_children_test_and_assert(TarFileUnpackHandler, EXPECTED_TAR_FILE_FORMAT)


def test_zip_unpacker():
    from lib.unpack import ZipFileUnpackHandler

    _archive_unpacker_children_test_and_assert(ZipFileUnpackHandler, EXPECTED_ZIP_FILE_FORMAT)


def test_targz_unpacker():
    from lib.unpack import TarGzFileUnpackHandler

    _archive_unpacker_children_test_and_assert(TarGzFileUnpackHandler, EXPECTED_TGZ_FILE_FORMAT)


def _mock_enumerate_guestfs_partitions(mock_mount_tools, return_value):
    mock_mount_tools.enumerate_guestfs_partitions.return_value = return_value


def _assert_guestfs_unpack_calls(mock_mount_tools, expected_tmp_dir, expected_partitions):
    mock_mount_tools.enumerate_guestfs_partitions.assert_called_once_with(EXPECTED_ARCHIVE_PATH)

    mock_mount_tools.mount_guestfs_partition.has_calls(
        [call(EXPECTED_ARCHIVE_PATH, x, expected_tmp_dir) for x in expected_partitions], any_order=True)


def test_guestfs_unpacker(mock_mount_tools):
    from lib.unpack import GuestFSFileUnpackHandler

    # For test output formatting... don't remove
    print()

    mock_u_ctx = _make_mock_u_ctx()
    _mock_enumerate_guestfs_partitions(mock_mount_tools, EXPECTED_GUESTFS_PARTITIONS)

    unpacker = GuestFSFileUnpackHandler(mock_u_ctx)
    _assert_base_file_handler_init_behavior(mock_u_ctx)

    unpack_ctx = unpacker.unpack()

    assert unpack_ctx == mock_u_ctx

    _assert_guestfs_unpack_calls(mock_mount_tools, EXPECTED_TMP_DIR, EXPECTED_GUESTFS_PARTITIONS)


def test_guestfs_unpacker_enumerate_error(mock_mount_tools):
    from lib.unpack import GuestFSFileUnpackHandler

    # For test output formatting... don't remove
    print()

    mock_u_ctx = _make_mock_u_ctx()
    mock_mount_tools.enumerate_guestfs_partitions.side_effect = MountException('some_mount_exception')

    unpacker = GuestFSFileUnpackHandler(mock_u_ctx)
    _assert_base_file_handler_init_behavior(mock_u_ctx)

    with pytest.raises(click.FileError) as e:
        unpacker.unpack()

    assert str(e.value) == f'Unable to list partitions for {EXPECTED_ARCHIVE_PATH}, aborting unpack'

    mock_mount_tools.enumerate_guestfs_partitions.assert_called_once_with(EXPECTED_ARCHIVE_PATH)
    mock_mount_tools.mount_guestfs_partition.assert_not_called()


def test_guestfs_unpacker_mount_error(mock_mount_tools):
    from lib.unpack import GuestFSFileUnpackHandler

    # For test output formatting... don't remove
    print()

    mock_u_ctx = _make_mock_u_ctx()
    _mock_enumerate_guestfs_partitions(mock_mount_tools, EXPECTED_GUESTFS_PARTITIONS)
    mock_mount_tools.mount_guestfs_partition.side_effect = MountException('some_mount_exception')

    unpacker = GuestFSFileUnpackHandler(mock_u_ctx)
    _assert_base_file_handler_init_behavior(mock_u_ctx)

    # Errors during mount doesn't stop the logic
    unpacker.unpack()

    _assert_guestfs_unpack_calls(mock_mount_tools, EXPECTED_TMP_DIR, EXPECTED_GUESTFS_PARTITIONS)


def test_dir_unpacker():
    from lib.unpack import DirFileUnpackHandler

    mock_u_ctx = _make_mock_u_ctx()

    unpacker = DirFileUnpackHandler(mock_u_ctx)

    unpack_ctx = unpacker.unpack()

    assert unpack_ctx == mock_u_ctx

    mock_u_ctx.create_tmp_dir.assert_not_called()


def test_is_handled_filetype():
    from lib.unpack import is_handled_filetype
    meta = common.make_file_meta('some_path')
    for filetype in EXPECTED_HANDLED_FILE_TYPES:
        meta.filetype = filetype
        assert is_handled_filetype(meta)

    meta.filetype = FileType.DOES_NOT_EXIST
    assert not is_handled_filetype(meta)


def test_unpack(mock_shutil, mock_contexts):
    from lib.unpack import unpack

    expected_file_meta = _make_file_meta()
    mock_u_ctx = _make_mock_u_ctx()
    mock_contexts.UnpackContext.return_value = mock_u_ctx

    unpack_ctx = unpack(expected_file_meta, EXPECTED_TMP_DIR_PARENT)

    mock_shutil.unpack_archive.assert_called_once_with(EXPECTED_ARCHIVE_PATH, EXPECTED_TMP_DIR,
                                                       format=EXPECTED_TAR_FILE_FORMAT)

    _assert_base_file_handler_init_behavior(unpack_ctx)


def test_unpack_unhandled_filetype(mock_contexts):
    from lib.unpack import unpack

    expected_file_meta = _make_file_meta()
    expected_file_meta.filetype = FileType.DOES_NOT_EXIST
    mock_u_ctx = _make_mock_u_ctx()
    mock_u_ctx.file_meta = expected_file_meta
    mock_contexts.UnpackContext.return_value = mock_u_ctx

    with pytest.raises(click.BadParameter) as e:
        unpack(expected_file_meta, EXPECTED_TMP_DIR_PARENT)

    assert str(e.value) == f'Unhandled file type: {FileType.DOES_NOT_EXIST}'


def test_unpack_archive_exception(mock_shutil, mock_contexts):
    from lib.unpack import unpack

    expected_archive_exception_str = 'some_archive_exception'

    expected_file_meta = _make_file_meta()
    mock_u_ctx = _make_mock_u_ctx()
    mock_contexts.UnpackContext.return_value = mock_u_ctx

    mock_shutil.unpack_archive.side_effect = Exception(expected_archive_exception_str)

    with pytest.raises(click.FileError) as e:
        unpack(expected_file_meta, EXPECTED_TMP_DIR_PARENT)

    assert str(
        e.value) == f'Unable to unpack {EXPECTED_ARCHIVE_PATH}, got the following error: {expected_archive_exception_str}'


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

EXPECTED_RECURSIVE_UNPACK_DIRS = {PARENT_ARCHIVE_UNPACK_DIR, VALID_ARCHIVE_1_UNPACK_DIR, VALID_ARCHIVE_2_UNPACK_DIR}


def _parent_archive_metadata() -> FileMetadata:
    file_meta = FileMetadata()
    file_meta.filetype = FileType.TAR
    file_meta.path = PARENT_ARCHIVE

    return file_meta


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


def _recursive_unpack_unpack_context_ctor_side_effect(*args, **kwargs):
    file_meta = args[0]

    u_ctx = MagicMock()

    u_ctx.file_meta = file_meta

    if file_meta.path == PARENT_ARCHIVE:
        u_ctx.unpacked_dir_location = PARENT_ARCHIVE_UNPACK_DIR
    elif file_meta.path == VALID_ARCHIVE_1:
        u_ctx.unpacked_dir_location = VALID_ARCHIVE_1_UNPACK_DIR
    elif file_meta.path == VALID_ARCHIVE_2:
        u_ctx.unpacked_dir_location = VALID_ARCHIVE_2_UNPACK_DIR

    return u_ctx


def test_unpack_recursive(mock_shutil, mock_contexts, mock_os, mock_file_data):
    from lib.unpack import unpack_recursive
    # For test output formatting... don't remove
    print()

    mock_contexts.UnpackContext.side_effect = _recursive_unpack_unpack_context_ctor_side_effect

    # mock_tmp_files.make_temp_dir.side_effect = _recursive_unpack_make_temp_dir_side_effect
    mock_os.walk.side_effect = _recursive_unpack_os_walk_side_effect
    mock_file_data.file_meta_from_path.side_effect = _recursive_unpack_file_meta_from_path_side_effect

    # Use real join
    mock_os.path.join = os.path.join

    parent_archive_meta = _parent_archive_metadata()

    unpack_ctxs = unpack_recursive(parent_archive_meta, 0, EXPECTED_TMP_DIR_PARENT)

    unpack_dirs = {x.unpacked_dir_location for x in unpack_ctxs}

    assert unpack_dirs == EXPECTED_RECURSIVE_UNPACK_DIRS
    # There are no call assertions here, since the only way that these two match is if all the
    # mocks got called correctly
