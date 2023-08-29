from unittest.mock import MagicMock, ANY

# noinspection PyPackageRequirements
import pytest
from pytest_mock import MockerFixture

from lib.exceptions import MountException


@pytest.fixture(scope='function')
def mock_os():
    return MagicMock()


@pytest.fixture(scope='function')
def mock_subprocess():
    return MagicMock()


@pytest.fixture(scope='function', autouse=True)
def setup_and_teardown(mocker: MockerFixture, mock_os, mock_subprocess):
    # Before logic
    # These are re-mocked for every single test
    mocker.patch('lib.mount_tools.os', mock_os)
    mocker.patch('lib.mount_tools.subprocess', mock_subprocess)

    yield
    # After logic
    # print('--AFTER--')
    pass


EXPECTED_STDOUT = 'some_test_output strings here'
EXPECTED_STDERR = 'some_test_error strings here'
GUESTFS_PARTITIONS = ['/dev/sda1', '/dev/sda2', '/dev/sda3']
GUESTFS_PARTITIONS_STR = '\n'.join(GUESTFS_PARTITIONS)
EXPECTED_GUESTFS_MOUNT_POINTS = ['++dev++sda1', '++dev++sda2', '++dev++sda3']
EXPECTED_FUSE_MOUNTS = ['/tmp/some_parent/++dev++sda1', '/tmp/some_parent/++dev++sda2', '/tmp/some_parent/++dev++sda3']
EXPECTED_FUSE_MOUNTS_STR = '\n'.join(EXPECTED_FUSE_MOUNTS)
EXPECTED_PARENT_TMP_DIR = '/tmp/some_parent_tmp_dir'
EXPECTED_ARCHIVE_PATH = '/tmp/some_archive_path.some_archive_format'


def _make_subprocess_result(stdout: str, stderr: str, returncode: int):
    result = MagicMock()
    result.stdout = stdout
    result.stderr = stderr
    result.returncode = returncode
    return result


def _call_enumerate_guestfs_parts():
    from lib.mount_tools import enumerate_guesfs_partitions
    return enumerate_guesfs_partitions(EXPECTED_ARCHIVE_PATH)


def test_enumerate_guestfs_parts(mock_subprocess):
    mock_subprocess.run.return_value = _make_subprocess_result(GUESTFS_PARTITIONS_STR, '', 0)

    assert _call_enumerate_guestfs_parts() == GUESTFS_PARTITIONS

    mock_subprocess.run.assert_called_once_with(['virt-filesystems', '-a', EXPECTED_ARCHIVE_PATH], capture_output=True,
                                                text=True)


def test_enumerate_guestfs_parts_error(mock_subprocess):
    mock_subprocess.run.return_value = _make_subprocess_result(EXPECTED_STDOUT, EXPECTED_STDERR, 1)

    with pytest.raises(MountException) as e:
        _call_enumerate_guestfs_parts()

    assert str(e.value) == EXPECTED_STDOUT + '\n' + EXPECTED_STDERR


# This doesn't have to match, since mocks, but looks nice
EXPECTED_MOUNT_POINT = f'{EXPECTED_PARENT_TMP_DIR}/{EXPECTED_GUESTFS_MOUNT_POINTS[0]}'


def _setup_mount_guestfs_partition(mock_os):
    mock_os.path.join.return_value = EXPECTED_MOUNT_POINT


def _assert_mount_guestfs_common_calls(mock_os):
    # Common calls include joining the path, and making the mount point directory
    mock_os.path.join.assert_called_once_with(EXPECTED_PARENT_TMP_DIR, EXPECTED_GUESTFS_MOUNT_POINTS[0])
    mock_os.mkdir.assert_called_once_with(EXPECTED_MOUNT_POINT)


def _call_mount_guestfs_partition():
    from lib.mount_tools import mount_guestfs_partition
    return mount_guestfs_partition(EXPECTED_ARCHIVE_PATH, GUESTFS_PARTITIONS[0], EXPECTED_PARENT_TMP_DIR)


def test_mount_guestfs_partition(mock_subprocess, mock_os):
    _setup_mount_guestfs_partition(mock_os)

    # Make subprocess call successful
    mock_subprocess.run.return_value = _make_subprocess_result('', '', 0)

    mount_point = _call_mount_guestfs_partition()
    assert mount_point == EXPECTED_MOUNT_POINT

    _assert_mount_guestfs_common_calls(mock_os)

    mock_subprocess.run.assert_called_once_with(
        ['guestmount', '-a', EXPECTED_ARCHIVE_PATH, '-m', GUESTFS_PARTITIONS[0], '--ro', EXPECTED_MOUNT_POINT],
        capture_output=True)


def test_mount_guestfs_partition_error(mock_subprocess, mock_os):
    from lib.mount_tools import mount_guestfs_partition

    _setup_mount_guestfs_partition(mock_os)

    # Make subprocess call fail
    mock_subprocess.run.return_value = _make_subprocess_result(EXPECTED_STDOUT, EXPECTED_STDERR, 1)

    with pytest.raises(MountException) as e:
        _call_mount_guestfs_partition()

    _assert_mount_guestfs_common_calls(mock_os)

    assert str(e.value) == EXPECTED_STDOUT + '\n' + EXPECTED_STDERR

    # Make sure that we remove the mount point if it fails
    mock_os.rmdir.assert_called_once_with(EXPECTED_MOUNT_POINT)


def _mount_iso():
    from lib.mount_tools import mount_iso
    mount_iso(EXPECTED_ARCHIVE_PATH, EXPECTED_PARENT_TMP_DIR)


def test_mount_iso(mock_subprocess):
    mock_subprocess.run.return_value = _make_subprocess_result('', '', 0)

    _mount_iso()

    mock_subprocess.run.assert_called_once_with(['mount', '-r', '-o', 'loop', EXPECTED_ARCHIVE_PATH,
                                                 EXPECTED_PARENT_TMP_DIR], capture_output=True)


def test_mount_iso_error(mock_subprocess):
    mock_subprocess.run.return_value = _make_subprocess_result(EXPECTED_STDOUT, EXPECTED_STDERR, 1)

    with pytest.raises(MountException) as e:
        _mount_iso()

    assert str(e.value) == EXPECTED_STDOUT + '\n' + EXPECTED_STDERR


should_return_good_fuse_mounts = True
should_guestfs_umount_succeed = True


def _guestfs_umount_run_side_effect(*args, **kwargs):
    global should_return_good_fuse_mounts, should_guestfs_umount_succeed

    if args[0] == ['mount', '-t', 'fuse']:
        if should_return_good_fuse_mounts:
            return _make_subprocess_result(EXPECTED_FUSE_MOUNTS_STR, '', 0)
        else:
            return _make_subprocess_result(EXPECTED_STDOUT, EXPECTED_STDERR, 1)
    elif args[0][0] == 'guestunmount':
        if should_guestfs_umount_succeed:
            return _make_subprocess_result('', '', 0)
        else:
            return _make_subprocess_result(EXPECTED_STDOUT, EXPECTED_STDERR, 1)

    _make_subprocess_result(EXPECTED_STDOUT, EXPECTED_STDERR, 1)


def _mock_guestfs_umount_run_actions(mock_subprocess, return_good_fuse_mounts: bool, umount_should_succeed: bool):
    global should_return_good_fuse_mounts, should_guestfs_umount_succeed

    should_return_good_fuse_mounts = return_good_fuse_mounts
    should_guestfs_umount_succeed = umount_should_succeed

    mock_subprocess.run.side_effect = _guestfs_umount_run_side_effect


def _assert_check_fuse_mounts_called(mock_subprocess):
    mock_subprocess.run.assert_any_call(['mount', '-t', 'fuse'], capture_output=True, text=True)


def _assert_guestunmount_called(mock_subprocess, mount_point):
    mock_subprocess.run.assert_any_call(['guestunmount', '--no-retry', mount_point], capture_output=True)


def _assert_guestumount_not_called(mock_subprocess):
    for call in mock_subprocess.run.mock_calls:
        assert 'guestunmount' not in call.args[0]


def _call_umount_guestfs_partition(directory):
    from lib.mount_tools import umount_guestfs_partition
    umount_guestfs_partition(directory)


def test_umount_guestfs_partition(mock_subprocess):
    _mock_guestfs_umount_run_actions(mock_subprocess, True, True)

    _call_umount_guestfs_partition(EXPECTED_FUSE_MOUNTS[0])

    _assert_check_fuse_mounts_called(mock_subprocess)
    _assert_guestunmount_called(mock_subprocess, EXPECTED_FUSE_MOUNTS[0])


def test_umount_guestfs_partition_no_fuse_mount(mock_subprocess):
    _mock_guestfs_umount_run_actions(mock_subprocess, False, True)

    _call_umount_guestfs_partition(EXPECTED_FUSE_MOUNTS[0])

    _assert_check_fuse_mounts_called(mock_subprocess)
    _assert_guestumount_not_called(mock_subprocess)


def test_umount_guestfs_partition_wrong_fuse_mount(mock_subprocess):
    _mock_guestfs_umount_run_actions(mock_subprocess, True, True)

    _call_umount_guestfs_partition('/tmp/some_other_mount')

    _assert_check_fuse_mounts_called(mock_subprocess)
    _assert_guestumount_not_called(mock_subprocess)


def test_umount_guestfs_partition_umount_error(mock_subprocess):
    _mock_guestfs_umount_run_actions(mock_subprocess, True, False)

    with pytest.raises(MountException) as e:
        _call_umount_guestfs_partition(EXPECTED_FUSE_MOUNTS[0])

    _assert_check_fuse_mounts_called(mock_subprocess)
    _assert_guestunmount_called(mock_subprocess, EXPECTED_FUSE_MOUNTS[0])

    assert str(e.value) == EXPECTED_STDOUT + '\n' + EXPECTED_STDERR


def test_umount_iso(mock_subprocess):
    from lib.mount_tools import umount_iso
    mock_subprocess.run.return_value = _make_subprocess_result('', '', 0)

    umount_iso(EXPECTED_ARCHIVE_PATH)

    mock_subprocess.run.assert_called_once_with(['umount', EXPECTED_ARCHIVE_PATH], capture_output=True)


def test_umount_iso_failed(mock_subprocess):
    from lib.mount_tools import umount_iso
    mock_subprocess.run.return_value = _make_subprocess_result(EXPECTED_STDOUT, EXPECTED_STDERR, 1)

    with pytest.raises(MountException) as e:
        umount_iso(EXPECTED_ARCHIVE_PATH)

    mock_subprocess.run.assert_called_once_with(['umount', EXPECTED_ARCHIVE_PATH], capture_output=True)

    assert str(e.value) == EXPECTED_STDOUT + '\n' + EXPECTED_STDERR
