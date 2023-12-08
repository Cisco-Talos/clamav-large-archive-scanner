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
