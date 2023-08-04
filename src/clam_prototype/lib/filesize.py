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
            return int(human_bytes)
        except ValueError:
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
    return int(size) * FILESIZE_UNITS[unit]
