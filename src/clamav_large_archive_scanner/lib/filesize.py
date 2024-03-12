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


from _decimal import InvalidOperation
from decimal import Decimal

# Stops at Terabytes, because Cisco doesn't generate binaries beyond that
FILESIZE_UNITS = {
    'B': 1,
    'K': 1024,
    'M': 1024 * 1024,
    'G': 1024 * 1024 * 1024,
    'T': 1024 * 1024 * 1024 * 1024,
}
VALID_FILESIZE_UNITS = FILESIZE_UNITS.keys()


# Convert human-readable file size to machine-readable file size
#
# Logic is a bit funky, basically looks for the first recognized unit and then multiplies by the appropriate factor
def convert_human_to_machine_bytes(human_bytes: str):
    human_bytes = human_bytes.upper()

    # Try to find a valid unit
    if not any(unit in human_bytes for unit in VALID_FILESIZE_UNITS):
        # No units, perhaps just an integer
        try:
            return Decimal(human_bytes)
        except InvalidOperation:
            pass

        raise ValueError(f'Invalid filesize unit in {human_bytes}')

    unit = ''
    # Find the first valid unit
    for c in human_bytes:
        if c in VALID_FILESIZE_UNITS:
            unit = c
            break

    # Split the string into the number and the unit, then calculate the size
    size = human_bytes.split(unit)[0]

    try:
        # There is always the chance that the user specified something like 7zM, which will be caught here
        return Decimal(size) * FILESIZE_UNITS[unit]
    except InvalidOperation:
        raise ValueError(f'{size} is not a valid number')
