# noinspection PyPackageRequirements
import pytest


def test_convert_human_to_machine_bytes():
    from lib.filesize import convert_human_to_machine_bytes

    assert convert_human_to_machine_bytes('12345') == 12345
    assert convert_human_to_machine_bytes('2B') == 2
    assert convert_human_to_machine_bytes('3k') == 3 * 1024
    assert convert_human_to_machine_bytes('40M') == 40 * 1024 * 1024
    assert convert_human_to_machine_bytes('100g') == 100 * 1024 * 1024 * 1024
    assert convert_human_to_machine_bytes('1.5T') == 1024 * 1024 * 1024 * 1024 * 1.5

    # Corner cases of specifying multiple units, should just take the first one
    assert convert_human_to_machine_bytes('1.5TB') == 1024 * 1024 * 1024 * 1024 * 1.5


def test_convert_human_to_machine_bytes_invalid():
    from lib.filesize import convert_human_to_machine_bytes
    with pytest.raises(ValueError) as e:
        convert_human_to_machine_bytes('1.5Z')

    assert str(e.value) == 'Invalid filesize unit in 1.5Z'

    # Corner case of invalid unit with multiple units
    with pytest.raises(ValueError) as e:
        convert_human_to_machine_bytes('1.5ZMb')

    assert str(e.value) == '1.5Z is not a valid number'
