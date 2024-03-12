# ClamAV Large Archive Scanner

The ClamAV Large Archive Scanner utility is a wrapper around the ClamAV `clamd` and `clamdscan` programs that provides a way to scan archives which exceed ClamAV's maximum file size limit. At the time of writing (2024/03/09), ClamAV may not scan any file or archive larger than 2 GiB.

> _Important_: This utility is a workaround to supplement ClamAV until such time as archives larger than 2 GiB can be scanned. This utility is *not* intended to replace `clamscan` or `clamdscan`. We have no intention of providing feature parity between this utility and `clamscan` or `clamdscan`.
>
> This utility works around ClamAV's file size limitations for non-archive files. It will not enable you scan large documents, graphics, videos, etc. In case you were wondering if large files could be chunked into smaller files and then scanned... No. That is not an effective solution to scan large files.

The utility has three sub-commands: `scan`, `unpack`, and `cleanup`.

The `scan` command combines the other two commands to unpack, scan, and clean up.

The `unpack` command provides the ability extract archives or mount disk images of the supported archive types without scanning them.

The `cleanup` command is complementary to the `unpack` command, enabling you to easily un-mount or delete the extracted archive contents.

## Supported Archive Types

The ClamAV Large Archive Scanner supports extraction or mounting of the following types of archives:
* TAR
* ZIP
* ISO
* VMDK
* TARGZ
* QCOW2

## Installation

We provide two options for installation. You may run the utility in your local environment or you may run the utility in a Docker container. The Docker container is easier.

### Running in Your Local Environment

To use the ClamAV Large Archive Scanner in your local environment, you will need to install an assortment of supporting tools and libraries:

* Install **Python 3.9** or newer.

* Install **the required Python packages**. We suggest using a [`venv` virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/). From the project root directory, run the following:
  ```sh
  python3 -m venv .venv
  source .venv/bin/activate
  pip3 install .
  ```

  If you open a new terminal, you will need to reactivate your Python virtual environment again, using: `source .venv/bin/activate`

* Install **ClamAV**. Both `clamd` and `clamdscan` are required. On some Linux distributions, these are packaged separately.  You can verify that they are present by running `which clamd` and `which clamdscan`.

* Install **libmagic** which is required to determine file types.

* Install **libguestfs** which is needed to unpack VMDK/QCOW2 disk images.

You will need to start the `clamd` service before you can use the ClamAV Large Archive Scanner. This may require some initial configuration to include using `freshclam` to download the latest malware detection signatures. See [the ClamAV documentation](https://docs.clamav.net/manual/Usage.html) for more information on how to set up ClamAV.

After you've installed everything and started `clamd`, you may run a scan with the ClamAV Large Archive Scanner. For example:
```sh
archive scan /path/to/archive
```

> _Tip_: If you have multiple ClamAV installations outside the normal `$PATH`, you may need to add the `bin` directory for your preferred version to the `$PATH` before attempting a scan.
>
> For example:
> ```sh
> PATH=~/clams/1.3.0/bin:$PATH
>
> archive scan /path/to/archive
> ```

To learn more, run `archive --help`, or keep skip to [Usage](#usage).

### Running in a Docker Container

The simplest way to use the ClamAV Large Archive Scanner is using a Docker container.

The provided `Dockerfile` may be used to build an container with the environment and tools necessary to run this utility.

This Docker container is based on the ClamAV project's `clamav-debian` image. You can find additional instructions for how to customize and use this container [here](https://github.com/Cisco-Talos/clamav-docker/blob/main/clamav/README-debian.md).

> _Note_: Privileged mode will be needed for to mount ISO archives when they are unpacked.

To build the image, run:
```sh
docker build . -t clamav-large-archive-scanner --load
```

To start the container, run:
```sh
docker run \
    --interactive \
    --tty \
    --rm \
    --name "clam_container_01" \
    clamav-large-archive-scanner
```

> _Tip_: You may wish to mount a `/some/path` containing the archives you wish to scan as a volume in the container.  You can do so when starting the container, like this. Replace `/some/path` with the actual directory you wish to mount. The directory contents will be found within the running container under `/target`:
> ```sh
> docker run \
>     --interactive \
>     --tty \
>     --rm \
>     --mount type=bind,source=/some/path,target=/target \
>     --name "clam_container_01" \
>     clamav-large-archive-scanner
> ```

After the container is up and running, and after `clamd` has finished loading, you may execute commands in the running container, or open a shell in the running container to execute commands.

> _Tip_: Within the container, you can use `clamdscan --ping 100` to wait up to 100 second for `clamd` to finish loading. If `clamd` takes longer than 100 seconds to load, or fails to load, then the command will exit with a non-zero exit code. For example:
> ```sh
> docker exec --interactive --tty "clam_container_01" clamdscan --ping 100
> ```

Suppose you used the `--mount` option to mount a directory at `/target` containing `some_archive.tgz`, you might try scanning it like this:
```sh
docker exec --interactive --tty "clam_container_01" archive scan /target/some_archive.tgz
```

Or, to enter a shell in the container, run:
```sh
docker exec --interactive --tty "clam_container_01" /bin/bash
```

To shut down the container, run:
```sh
docker kill clam_container_01
```

## Usage

```
Usage: archive [OPTIONS] COMMAND [ARGS]...

Options:
  -t, --trace        Enable trace logging. By default, log all actions to
                     /tmp/clam_unpacker.log
  --trace-file PATH  Override the default trace log file
  -v, --verbose      Enable verbose logging
  -q, --quiet        Disable all logging
  --help             Show this message and exit.

Commands:
  cleanup
  scan
  unpack
```

### Commands

* `scan`

  This command is used to scan regular files and directories.

  The `scan` command combines the other two commands to unpack, scan, and clean up.

  Use the following options to customize scan behavior:

  ```
  Usage: archive scan [OPTIONS] PATH

  Options:
    --min-size TEXT   Minimum file size to unpack (default: 2.0 GiB).
    --ignore-size     Ignore file size lower limit (equivalent to --min-size=0).
    --tmp-dir PATH    Temporary working directory (default: /tmp).
    -ff, --fail-fast  Stop scanning after the first failure.
    --allmatch        Continue scanning if a signature match occurs.
    --help            Show this message and exit.
  ```

* `unpack`

  This command unpacks or mounts supported large archives to a given directory. By default, a "large" archive is a one greater than 2 GiB. This action is recursive.

  Archives smaller than 2 GiB will be skipped. You may use `--ignore-size` or `--min-size=0` unpack all supported archives, regardless of size.

  ```
  Usage: archive unpack [OPTIONS] PATH

  Options:
    -r, --recursive  Recursively unpack files.
    --min-size TEXT  Minimum file size to unpack (default: 2.0 GiB).
    --ignore-size    Ignore file size lower limit (equivalent to --min-size=0).
    --tmp-dir PATH   Directory to unpack files to (default: /tmp).
    --help           Show this message and exit.
  ```

* `cleanup`

  This command will clean up the temp directories/files created as part of the script to scan input file or directory.

  ```
  Usage: archive cleanup [OPTIONS] PATH

  Options:
    --file          Recursively cleanup directories associated with the file.
    --tmp-dir PATH  Directory to search for unpacked files(default: /tmp).
    --help          Show this message and exit.
  ```

## Examples

Using the `scan` command to scan an archive:
```sh
archive -t -v scan /path/to/archive
```

Using the `unpack` command to unpack and archive:
```sh
archive -t -v unpack /path/to/archive
```

## Contributing

[There are many ways to contribute](CONTRIBUTING.md).

## Unit Tests

This repo includes some tests to verify correct functionality. You can run the tests from your local environment or within the running Docker container.

1. First install ClamAV Large Archive Scanner utility one of the two ways.

2. Then run this to install the test prerequisites:
  ```sh
  source .venv/bin/activate
  pip3 install -r ./src/clamav_large_archive_scanner/test/requirements.txt
  ```

3. Now run the unit tests:
  ```sh
  pytest -v
  ````

## License

This project is licensed under [the BSD 3-Clause license](LICENSE).
