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

import click
import humanize

import lib.cleanup as cleaner
import lib.file_data as detect
import lib.unpack as unpacker
import lib.scanner as scanner
import lib.contexts as Contexts

from lib import fast_log
from lib.filesize import convert_human_to_machine_bytes

DEFAULT_MIN_SIZE_THRESHOLD_BYTES = 2 * 1024 * 1024 * 1024  # 2GB
DEFAULT_MIN_SIZE_HUMAN = humanize.naturalsize(DEFAULT_MIN_SIZE_THRESHOLD_BYTES, binary=True)


# You'll notice that several functions here are duplicated with _ in front of them
# This is to make UT easier, as trying to test some of the filesystem interactions is a bit tricky
# Best to just assume that all the click checks are passing, and only test our logic


@click.group()
@click.option('-t', '--trace', is_flag=True, default=False,
              help=f'Enable trace logging. By default, log all actions to {fast_log.LOG_FILE}')
@click.option('--trace-file', default=None, type=click.Path(resolve_path=True),
              help=f'Override the default trace log file')
@click.option('-v', '--verbose', is_flag=True, default=False, help='Enable verbose logging')
@click.option('-q', '--quiet', is_flag=True, default=False, help='Disable all logging')
def cli(trace, trace_file, verbose, quiet):
    if not quiet:
        fast_log.log_start(verbose, trace, trace_file)


# Since this is used multiple times, logic is held here
def _unpack(path: str, recursive: bool, min_size: str, ignore_size: bool, tmp_dir: str) -> list[Contexts.UnpackContext]:
    """
    :param path: Path to unpack
    :param recursive: Whether to recursively unpack
    :param min_size: Minimum file size to unpack
    :param tmp_dir: Temporary directory to unpack to
    :return: A list of unpacked directories
    """

    file_meta = detect.file_meta_from_path(path)

    fast_log.debug(f'Got file metadata: \n{file_meta}')

    if ignore_size:
        min_file_size = 0
    else:
        try:
            min_file_size = convert_human_to_machine_bytes(min_size)
        except ValueError as e:
            raise click.BadParameter(f'Unable to parse min-size: {e}')

    # In the special case where a directory is specified, we're just going to do recursive unpack on the dir
    if file_meta.filetype == detect.FileType.DIR:
        recursive = True

    else:
        # Check if filesize is < min-size for non directories
        # If so, do not try to unpack it, unless --ignore-size is passed
        if file_meta.size_raw < min_file_size:
            fast_log.warn(
                f'File size is below the threshold of {DEFAULT_MIN_SIZE_HUMAN}, not unpacking. See help for options')
            return []

    unpack_ctxs = []

    if recursive:
        unpack_ctxs = unpacker.unpack_recursive(file_meta, min_file_size, tmp_dir)
        fast_log.info('Found and unpacked the following:')
        fast_log.info('\n'.join([str(u_ctx) for u_ctx in unpack_ctxs]))
    else:
        u_ctx = unpacker.unpack(file_meta, tmp_dir)
        fast_log.info(f'Unpacked {u_ctx}')
        unpack_ctxs.append(u_ctx)

    return unpack_ctxs


@cli.command()
@click.argument('path', type=click.Path(exists=True, resolve_path=True))
# @click.argument('path', type=click.Path(exists=False, resolve_path=True))
@click.option('-r', '--recursive', is_flag=True, help='Recursively unpack files')
@click.option('--min-size', default=DEFAULT_MIN_SIZE_THRESHOLD_BYTES,
              help=f'Minimum file size to unpack (default: {DEFAULT_MIN_SIZE_HUMAN})', type=str)
@click.option('--ignore-size', default=False, is_flag=True,
              help='Ignore file size lower limit (equivalent to --min-size=0)')
@click.option('--tmp-dir', default='/tmp', type=click.Path(resolve_path=True),
              help='Directory to unpack files to (default: /tmp)')
def unpack(path, recursive, min_size, ignore_size, tmp_dir):
    _unpack(path, recursive, min_size, ignore_size, tmp_dir)


def _cleanup(path, is_file, tmp_dir):
    fast_log.info(f'Attempting to clean up {path}')

    if is_file:
        cleaner.cleanup_recursive(path, tmp_dir)
    else:
        cleaner.cleanup_path(path)

    fast_log.info(f'Cleaned up  {path}')


@cli.command()
@click.argument('path', type=click.Path(exists=True, resolve_path=True))
@click.option('--file', 'is_file', is_flag=True, help='Recursively cleanup directories associated with the file ')
@click.option('--tmp-dir', default='/tmp', type=click.Path(resolve_path=True),
              help='Directory to search for unpacked files(default: /tmp)')
def cleanup(path, is_file, tmp_dir):
    _cleanup(path, is_file, tmp_dir)


def _deepscan(path, min_size, ignore_size, fail_fast, all_match, tmp_dir):
    if not scanner.validate_clamdscan():
        raise click.ClickException(f'Unable to find clamdscan, please install it and try again')

    # all-match and ff cannot be both active
    if all_match and fail_fast:
        raise click.ClickException(f'Cannot specify both --allmatch and --fail-fast')

    # recursively unpack the file
    unpacked_ctxs = _unpack(path, True, min_size, ignore_size, tmp_dir)

    # scan the unpacked dirs
    files_clean = scanner.clamdscan(unpacked_ctxs, fail_fast, all_match)

    # Cleanup
    cleaner.cleanup_recursive(path, tmp_dir)

    if not files_clean:
        raise click.ClickException(f'Found virus in {path}')


@cli.command()
@click.argument('path', type=click.Path(exists=True, resolve_path=True))
@click.option('--min-size', default=DEFAULT_MIN_SIZE_THRESHOLD_BYTES,
              help=f'Minimum file size to unpack (default: {DEFAULT_MIN_SIZE_HUMAN})', type=str)
@click.option('--ignore-size', default=False, is_flag=True,
              help='Ignore file size lower limit (equivalent to --min-size=0)')
@click.option('--tmp-dir', default='/tmp', type=click.Path(resolve_path=True),
              help='Temporary working directory (default: /tmp)')
@click.option('-ff', '--fail-fast', default=False, is_flag=True,
              help='Stop scanning after the first failure')
@click.option('--allmatch', default=False, is_flag=True,
              help='Stop scanning after the first failure')
def deepscan(path, min_size, ignore_size, fail_fast, allmatch, tmp_dir):
    _deepscan(path, min_size, ignore_size, fail_fast, allmatch, tmp_dir)


if __name__ == "__main__":
    cli()
