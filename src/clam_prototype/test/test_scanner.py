import subprocess
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture


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


def _assert_run_clamdscan_called(mock_subprocess, path: str):
    mock_subprocess.run.assert_any_call(['clamdscan', '-m', '--stdout', path], capture_output=True, text=True)


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


EXPECTED_PATHS = ['some_path1', 'some_path2', 'some_path3']


def test_clamdscan_clean(mock_subprocess):
    from lib.scanner import clamdscan
    mock_subprocess.run.return_value = _make_subprocess_result('', '', 0)

    assert clamdscan(EXPECTED_PATHS, False)

    for path in EXPECTED_PATHS:
        _assert_run_clamdscan_called(mock_subprocess, path)


def test_clamdscan_virus_found(mock_subprocess):
    from lib.scanner import clamdscan
    mock_subprocess.run.return_value = _make_subprocess_result('', '', 1)

    assert not clamdscan(EXPECTED_PATHS, False)

    for path in EXPECTED_PATHS:
        _assert_run_clamdscan_called(mock_subprocess, path)


def _fail_second_path_side_effect(*args, **kwargs):
    if args[0][3] == EXPECTED_PATHS[1]:
        return _make_subprocess_result('', '', 1)
    else:
        return _make_subprocess_result('', '', 0)


def test_clamdsan_virus_found_fail_fast(mock_subprocess):
    from lib.scanner import clamdscan
    mock_subprocess.run.side_effect = _fail_second_path_side_effect

    assert not clamdscan(EXPECTED_PATHS, True)

    _assert_run_clamdscan_called(mock_subprocess, EXPECTED_PATHS[0])
    _assert_run_clamdscan_called(mock_subprocess, EXPECTED_PATHS[1])
    assert mock_subprocess.run.call_count == 2
