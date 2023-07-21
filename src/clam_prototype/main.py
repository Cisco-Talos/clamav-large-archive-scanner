

import click
import lib.detect as detect


@click.group()
def cli():
    pass


@cli.command()
@click.argument('path', type=click.Path(exists=True))
def unpack(path):
    file_meta = detect.get_metadata(path)

    print(f'Got file metadata: \n{file_meta}')
    pass


if __name__ == "__main__":
    cli()
