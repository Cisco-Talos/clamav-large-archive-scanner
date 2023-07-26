import click

import lib.unpack as unpacker
import lib.cleanup as cleaner

import lib.file_data as detect

DEFAULT_MIN_SIZE_THRESHOLD = 2 * 1024 * 1024 * 1024  # 2GB


@click.group()
def cli():
    pass


@cli.command()
@click.argument('path', type=click.Path(exists=True, resolve_path=True))
@click.option('-r', '--recursive', is_flag=True, help='Recursively unpack files')
@click.option('--ignore-size', default=False, is_flag=True, help='Ignore file size lower limit')
def unpack(path, recursive, ignore_size):
    file_meta = detect.file_meta_from_path(path)

    print(f'Got file metadata: \n{file_meta}')

    min_file_size = DEFAULT_MIN_SIZE_THRESHOLD
    if ignore_size:
        min_file_size = 0

    # Check if filesize is < 2GB
    # If so, do not try to unpack it, unless --ignore-size is passed
    if file_meta.size_raw < min_file_size:
        print('File size is below the threshold of 2gb, not unpacking. Use --ignore-size to force unpacking')
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
@click.option('-r', '--recursive', is_flag=True, help='Recursively cleanup directories associated with the file, --file is assumed to be true')
@click.option('--file', 'is_file', is_flag=True, help='Attempt to clean up using the file as a reference')
def cleanup(path, recursive, is_file):
    print(f'Attempting to clean up {path}')

    if recursive:
        cleaner.cleanup_recursive(path)
        print(f'Cleaned up recursively {path}')
    else:
        if not is_file:
            cleaner.cleanup_path(path)
        else:
            cleaner.cleanup_file(path)
        print(f'Cleaned up  {path}')


if __name__ == "__main__":
    cli()
