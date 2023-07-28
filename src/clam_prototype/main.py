import click
import humanize

import lib.unpack as unpacker
import lib.cleanup as cleaner

import lib.file_data as detect
from lib.filesize import convert_human_to_machine_bytes

DEFAULT_MIN_SIZE_THRESHOLD_BYTES = 2 * 1024 * 1024 * 1024  # 2GB
DEFAULT_MIN_SIZE_HUMAN = humanize.naturalsize(DEFAULT_MIN_SIZE_THRESHOLD_BYTES, binary=True)


@click.group()
def cli():
    pass


@cli.command()
@click.argument('path', type=click.Path(exists=True, resolve_path=True))
# @click.argument('path', type=click.Path(exists=False, resolve_path=True))
@click.option('-r', '--recursive', is_flag=True, help='Recursively unpack files')
@click.option('--min-size', default=DEFAULT_MIN_SIZE_THRESHOLD_BYTES,
              help=f'Minimum file size to unpack (default: {DEFAULT_MIN_SIZE_HUMAN})', type=str)
@click.option('--ignore-size', default=False, is_flag=True,
              help='Ignore file size lower limit (equivalent to --min-size=0)')
def unpack(path, recursive, min_size, ignore_size):
    file_meta = detect.file_meta_from_path(path)

    print(f'Got file metadata: \n{file_meta}')

    min_file_size = convert_human_to_machine_bytes(min_size)

    if ignore_size:
        min_file_size = 0

    # In the special case where a directory is specified, we're just going to do recursive unpack on the dir
    if file_meta.filetype == detect.FileType.DIR:
        recursive = True

    else:
        # Check if filesize is < min-size for non directories
        # If so, do not try to unpack it, unless --ignore-size is passed
        if file_meta.size_raw < min_file_size:
            print(
                f'File size is below the threshold of {DEFAULT_MIN_SIZE_HUMAN}, not unpacking. See help for options')
            return

    if recursive:
        unpack_dirs = unpacker.unpack_recursive(file_meta, min_file_size)
        print('Found and unpacked the following:')
        print('\n'.join(unpack_dirs))
    else:
        unpack_dir = unpacker.unpack(file_meta)
        print(f'Unpacked File to {unpack_dir}')


@cli.command()
@click.argument('path', type=click.Path(exists=True, resolve_path=True))
@click.option('--file', 'is_file', is_flag=True, help='Recursively cleanup directories associated with the file ')
def cleanup(path, is_file):
    print(f'Attempting to clean up {path}')

    if is_file:
        cleaner.cleanup_recursive(path)
    else:
        cleaner.cleanup_path(path)

    print(f'Cleaned up  {path}')


if __name__ == "__main__":
    cli()
