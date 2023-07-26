import click
import lib.file_data as detect
import lib.unpackers as unpackers


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
    file_meta = detect.FileMetadata.from_path(path)

    print(f'Got file metadata: \n{file_meta}')

    # TODO: Check filesize here

    if recursive:
        print("Recursively unpacking is not yet supported")
        unpackers.unpack_recursive(file_meta)
    else:
        unpack_dir = unpackers.unpack(file_meta)
        print(f'Unpacked File to {unpack_dir}')


if __name__ == "__main__":
    cli()
