import click

import lib.unpack as unpacker
import lib.cleanup as cleaner

import lib.file_data as detect


def _debug():
    fm = detect.FileMetadata.from_path('/home/yanbzhu/clamAV/huge/boot.vmdk')

    print(fm)

    js = fm.as_json()
    print(js)

    fm2 = detect.FileMetadata.from_json(js)
    print(fm2)


@click.group()
def cli():
    pass


@cli.command()
@click.argument('path', type=click.Path(exists=True, resolve_path=True))
@click.option('-r', '--recursive', is_flag=True, help='Recursively unpack files')
def unpack(path, recursive):
    file_meta = detect.file_meta_from_path(path)

    print(f'Got file metadata: \n{file_meta}')

    # TODO: Check filesize here

    if recursive:
        print("Recursively unpacking is not yet supported")
        unpacker.unpack_recursive(file_meta)
    else:
        unpack_dir = unpacker.unpack(file_meta)
        print(f'Unpacked File to {unpack_dir}')


@cli.command()
@click.argument('path', type=click.Path(exists=True, resolve_path=True))
@click.option('-r', '--recursive', is_flag=True, help='Recursively unpack files')
@click.option('--is-file', is_flag=True, help='Attempt to clean up using the file as a reference')
def cleanup(path, recursive, is_file):

    print(f'Attempting to clean up {path}')

    if recursive:
        print("Recursively unpacking is not yet supported")
    else:
        if not is_file:
            cleaner.cleanup_path(path)
        else:
            cleaner.cleanup_file(path)
        print(f'Cleaned up  {path}')


if __name__ == "__main__":
    cli()
