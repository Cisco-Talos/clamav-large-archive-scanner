

import click
import lib.detect as detect
import lib.unpackers as unpackers

@click.group()
def cli():
    pass


@cli.command()
@click.argument('path', type=click.Path(exists=True))
def unpack(path):
    file_meta = detect.get_metadata(path)

    print(f'Got file metadata: \n{file_meta}')

    unpackers.unpack(file_meta)



if __name__ == "__main__":
    cli()
