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
