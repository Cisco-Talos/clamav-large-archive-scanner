# This mainly exists to make UT and Mocks easier to write, but it also makes the code a bit more readable
# Path: lib/file_data.py
import os
import subprocess


class MountException(Exception):
    pass


def enumerate_guesfs_partitions(file_path: str) -> list[str]:
    result = subprocess.run(['virt-filesystems', '-a', file_path], capture_output=True, text=True)
    if result.returncode != 0:
        combined_output = str(result.stdout) + '\n' + str(result.stderr)
        raise MountException(combined_output)

    partitions = [x for x in result.stdout.split('\n') if x != '']
    return partitions


def mount_guestfs_partition(archive_path: str, partition: str, parent_tmp_dir: str) -> str:
    # Make a dir for the partition inside the mount_parent_dir
    # most partitions though, will contain the "/" character, so we need to replace it
    tmp_partition_name = partition.replace('/', '++')
    partition_tmp_dir = os.path.join(parent_tmp_dir, tmp_partition_name)

    os.mkdir(partition_tmp_dir)

    # Actually use guestmount to mount it
    # guestmount -a /workspace/boot.vmdk -m /dev/sda1  --ro /workspace/t
    result = subprocess.run(['guestmount', '-a', archive_path, '-m', partition, '--ro', partition_tmp_dir])
    if result.returncode != 0:
        # Could not mount, should remove directory
        os.rmdir(partition_tmp_dir)
        combined_output = str(result.stdout) + '\n' + str(result.stderr)
        raise MountException(combined_output)

    return partition_tmp_dir


def mount_iso(file_path: str, mount_point: str) -> None:
    result = subprocess.run(['mount', '-r', '-o', 'loop', file_path, mount_point])
    if result.returncode != 0:
        combined_output = str(result.stdout) + '\n' + str(result.stderr)
        raise MountException(combined_output)


def umount_guestfs_partition(directory: str) -> None:

    # guestunmount local_dir
    result = subprocess.run(['guestunmount', directory])
    if result.returncode != 0:
        combined_output = str(result.stdout) + '\n' + str(result.stderr)
        raise MountException(combined_output)


def umount_iso(mount_point: str) -> None:
    result = subprocess.run(['umount', mount_point])
    if result.returncode != 0:
        combined_output = str(result.stdout) + '\n' + str(result.stderr)
        raise MountException(combined_output)