import stat
from unittest.mock import MagicMock

# noinspection PyPackageRequirements
import pytest
from pytest_mock import MockerFixture

from lib.file_data import FileType

EXPECTED_TEST_PATH = '/tmp/some_test_path'


@pytest.fixture(scope='function')
def mock_os():
    return MagicMock()


@pytest.fixture(scope='function')
def mock_magic():
    return MagicMock()


@pytest.fixture(scope='function', autouse=True)
def setup_and_teardown(mocker: MockerFixture, mock_os, mock_magic):
    # Before logic
    # These are re-mocked for every single test
    mocker.patch('lib.file_data.os', mock_os)
    mocker.patch('lib.file_data.magic', mock_magic)

    yield
    # After logic
    # print('--AFTER--')
    pass


def test_file_meta_get_filename():
    from lib.file_data import FileMetadata

    file_meta = FileMetadata()
    file_meta.path = EXPECTED_TEST_PATH

    assert file_meta.get_filename() == 'some_test_path'


def test_get_filetype_from_desc():
    from lib.file_data import _get_filetype
    assert _get_filetype('POSIX tar archive') == FileType.TAR
    assert _get_filetype('Zip archive data') == FileType.ZIP
    assert _get_filetype('ISO 9660 CD-ROM filesystem data') == FileType.ISO
    assert _get_filetype('VMware4 disk image') == FileType.VMDK
    assert _get_filetype('gzip compressed data') == FileType.TARGZ
    assert _get_filetype('QEMU QCOW2 Image') == FileType.QCOW2
    assert _get_filetype('Strange File Type') == FileType.UNKNOWN


def _mock_file_type_regular(mock_os_in, is_regular: bool):
    mocked_file_stat = MagicMock()

    mock_os_in.lstat.return_value = mocked_file_stat
    if is_regular:
        mocked_file_stat.st_mode = stat.S_IFREG

        # Since we're mocking that it's a regular file, we need to mock that it's not a directory
        _mock_is_dir(mock_os_in, False)
    else:
        mocked_file_stat.st_mode = stat.S_IFDOOR


def test_is_regular_file(mock_os):
    from lib.file_data import _is_regular_file

    _mock_file_type_regular(mock_os, True)
    assert _is_regular_file(EXPECTED_TEST_PATH) is True

    mock_os.lstat.assert_called_once_with(EXPECTED_TEST_PATH)
    mock_os.reset_mock()

    _mock_file_type_regular(mock_os, False)
    assert _is_regular_file(EXPECTED_TEST_PATH) is False

    mock_os.lstat.assert_called_once_with(EXPECTED_TEST_PATH)


def _mock_path_exists(mock_os, exists):
    mock_os.path.exists.return_value = exists


def _mock_is_dir(mock_os, is_dir):
    mock_os.path.isdir.return_value = is_dir


def test_file_meta_from_path(mock_os, mock_magic):
    from lib.file_data import file_meta_from_path
    _mock_file_type_regular(mock_os, True)
    _mock_path_exists(mock_os, True)

    mock_magic.from_file.return_value = 'QEMU QCOW2 Image (v3),'

    expected_file_size = 1234
    mock_os.path.getsize.return_value = expected_file_size

    file_meta = file_meta_from_path(EXPECTED_TEST_PATH)

    assert file_meta.path == EXPECTED_TEST_PATH
    assert file_meta.desc == 'QEMU QCOW2 Image (v3),'
    assert file_meta.size_raw == expected_file_size
    assert file_meta.filetype == FileType.QCOW2

    mock_os.path.exists.assert_called_once_with(EXPECTED_TEST_PATH)
    mock_os.path.getsize.assert_called_once_with(EXPECTED_TEST_PATH)
    mock_magic.from_file.assert_called_once_with(EXPECTED_TEST_PATH, mime=False)


def test_file_meta_from_path_is_dir(mock_os, mock_magic):
    from lib.file_data import file_meta_from_path
    _mock_is_dir(mock_os, True)
    _mock_file_type_regular(mock_os, False)
    _mock_path_exists(mock_os, True)

    file_meta = file_meta_from_path(EXPECTED_TEST_PATH)

    assert file_meta.path == EXPECTED_TEST_PATH
    assert file_meta.desc == 'Directory'
    assert file_meta.size_raw == 0
    assert file_meta.filetype == FileType.DIR

    mock_os.path.exists.assert_called_once_with(EXPECTED_TEST_PATH)
    mock_os.path.getsize.assert_not_called()
    mock_magic.from_file.assert_not_called()


def test_file_meta_from_path_unknown(mock_os, mock_magic):
    from lib.file_data import file_meta_from_path

    _mock_file_type_regular(mock_os, False)
    _mock_is_dir(mock_os, False)
    _mock_path_exists(mock_os, True)

    mock_magic.from_file.return_value = 'Some unknown file type'

    file_meta = file_meta_from_path(EXPECTED_TEST_PATH)

    assert file_meta.path == EXPECTED_TEST_PATH
    assert file_meta.desc == 'Unknown file type'
    assert file_meta.size_raw == 0
    assert file_meta.filetype == FileType.UNKNOWN

    mock_os.path.exists.assert_called_once_with(EXPECTED_TEST_PATH)
    mock_os.path.getsize.assert_not_called()
    mock_magic.from_file.assert_not_called()


def test_file_meta_from_path_does_not_exist(mock_os, mock_magic):
    from lib.file_data import file_meta_from_path

    _mock_path_exists(mock_os, False)

    file_meta = file_meta_from_path(EXPECTED_TEST_PATH)

    assert file_meta.path == EXPECTED_TEST_PATH
    assert file_meta.desc == 'File does not exist'

    mock_os.path.exists.assert_called_once_with(EXPECTED_TEST_PATH)
    mock_os.path.getsize.assert_not_called()
    mock_magic.from_file.assert_not_called()
