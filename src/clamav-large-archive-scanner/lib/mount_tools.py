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

# This mainly exists to make UT and Mocks easier to write, but it also makes the code a bit more readable
import os
import subprocess

from lib.exceptions import MountException
from lib.fast_log import trace


def enumerate_guestfs_partitions(file_path: str) -> list[str]:
    result = subprocess.run(['virt-filesystems', '-a', file_path], capture_output=True, text=True)
    if result.returncode != 0:
        combined_output = str(result.stdout) + '\n' + str(result.stderr)
        raise MountException(combined_output)

    partitions = [x for x in result.stdout.split('\n') if x != '']
    return partitions


def _check_fuse_mounts() -> list[str]:
    result = subprocess.run(['mount', '-t', 'fuse'], capture_output=True, text=True)
    if result.returncode != 0:
        trace(f'Unable to enumerate fuse mounts: {result.stderr}')
        return []

    mounts = [x for x in result.stdout.split('\n') if x != '']
    return mounts


def mount_guestfs_partition(archive_path: str, partition: str, parent_tmp_dir: str) -> str:
    # Make a dir for the partition inside the mount_parent_dir
    # most partitions though, will contain the "/" character, so we need to replace it
    tmp_partition_name = partition.replace('/', '++')
    partition_tmp_dir = os.path.join(parent_tmp_dir, tmp_partition_name)
    os.mkdir(partition_tmp_dir)

    # Actually use guestmount to mount it
    # guestmount -a /workspace/boot.vmdk -m /dev/sda1  --ro /workspace/t
    result = subprocess.run(['guestmount', '-o', 'allow_other', '-a', archive_path, '-m', partition, '--ro', partition_tmp_dir],
                            capture_output=True)
    if result.returncode != 0:
        # Could not mount, should remove directory
        os.rmdir(partition_tmp_dir)
        combined_output = str(result.stdout) + '\n' + str(result.stderr)
        raise MountException(combined_output)

    return partition_tmp_dir


def mount_iso(file_path: str, mount_point: str) -> None:
    result = subprocess.run(['mount', '-r', '-o', 'loop', file_path, mount_point], capture_output=True)
    if result.returncode != 0:
        combined_output = str(result.stdout) + '\n' + str(result.stderr)
        raise MountException(combined_output)


def umount_guestfs_partition(directory: str) -> None:
    # Check to see if it still mounted
    fuse_mounts = _check_fuse_mounts()

    if not any(directory in m for m in fuse_mounts):
        trace(f'Partition {directory} is not mounted, skipping umount')
        return

    # guestunmount local_dir
    result = subprocess.run(['guestunmount', '--no-retry', directory], capture_output=True)
    if result.returncode != 0:
        combined_output = str(result.stdout) + '\n' + str(result.stderr)
        raise MountException(combined_output)


def umount_iso(mount_point: str) -> None:
    result = subprocess.run(['umount', mount_point], capture_output=True)
    if result.returncode != 0:
        combined_output = str(result.stdout) + '\n' + str(result.stderr)
        raise MountException(combined_output)


def list_top_level_dirs(path: str) -> list[str]:
    dirs = []
    for a_dir in os.listdir(path):
        full_path = os.path.join(path, a_dir)
        if os.path.isdir(full_path):
            dirs.append(full_path)

    return dirs
