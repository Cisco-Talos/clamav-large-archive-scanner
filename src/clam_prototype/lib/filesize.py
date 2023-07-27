# Convert human-readable file size to machine-readable file size
# Stops at Terabytes, because Cisco doesn't generate binaries beyond that
def convert_human_to_machine_bytes(human_bytes: str):

    human_bytes = human_bytes.upper()

    if 'K' in human_bytes:
        return int(human_bytes[:-1]) * 1024
    elif 'M' in human_bytes:
        return int(human_bytes[:-1]) * 1024 * 1024
    elif 'G' in human_bytes:
        return int(human_bytes[:-1]) * 1024 * 1024 * 1024
    elif 'T' in human_bytes:
        return int(human_bytes[:-1]) * 1024 * 1024 * 1024 * 1024
    else:
        return int(human_bytes)

