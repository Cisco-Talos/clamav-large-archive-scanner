# Copyright (C) 2023-2024 Cisco Systems, Inc. and/or its affiliates. All rights reserved.
#
# Authors: Dave Zhu (yanbzhu@cisco.com)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of mosquitto nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# noinspection PyPackageRequirements
import pytest


def test_convert_human_to_machine_bytes():
    from clamav_large_archive_scanner.lib.filesize import convert_human_to_machine_bytes

    assert convert_human_to_machine_bytes('12345') == 12345
    assert convert_human_to_machine_bytes('2B') == 2
    assert convert_human_to_machine_bytes('3k') == 3 * 1024
    assert convert_human_to_machine_bytes('40M') == 40 * 1024 * 1024
    assert convert_human_to_machine_bytes('100g') == 100 * 1024 * 1024 * 1024
    assert convert_human_to_machine_bytes('1.5T') == 1024 * 1024 * 1024 * 1024 * 1.5

    # Corner cases of specifying multiple units, should just take the first one
    assert convert_human_to_machine_bytes('1.5TB') == 1024 * 1024 * 1024 * 1024 * 1.5


def test_convert_human_to_machine_bytes_invalid():
    from clamav_large_archive_scanner.lib.filesize import convert_human_to_machine_bytes
    with pytest.raises(ValueError) as e:
        convert_human_to_machine_bytes('1.5Z')

    assert str(e.value) == 'Invalid filesize unit in 1.5Z'

    # Corner case of invalid unit with multiple units
    with pytest.raises(ValueError) as e:
        convert_human_to_machine_bytes('1.5ZMb')

    assert str(e.value) == '1.5Z is not a valid number'
