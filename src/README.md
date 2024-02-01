# ClamAV Large Archive Scanner

This python CLI utility is a wrapper around clamdscan to provide a way to scan files exceeding clamav max file size.
The utility has three sub-commands: deepscan, unpack, and cleanup. Command "deepscan" runs unpack, scans with clamdscan,
then runs cleanup.

## Supported File Types
    TAR 
    ZIP 
    ISO 
    VMDK 
    TARGZ
    QCOW2

## Installation
### Source Code
* Install required packages using python **>v3.9** to install requirement.txt
  * Install python3 and virtual env using https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/
  * install packages using  ```python3 -m pip install -r <project-root>src/clam_prototype/requirements.txt/requirements.txt``` 
* Install **clamdscan** so that it is accessible to the script (Try: ```which clamdscan```).
* Install **libmagic** which is required to determine file types.
* Install **libguestfs** which is needed to unpack VMDK/QCOW2 disk images.

### Docker
A dockerfile "Dockerfile.scanner.in.clam" can be run to get clamav and python scan-cli utility to be used.
Docker-run will install clamav, required packages like libguestfs-tools and copy the python src code to be run. 

## Usage
```
Usage: main.py [OPTIONS] COMMAND [ARGS]...

Options:
  -t, --trace        Enable trace logging. By default, log all actions to
                     /tmp/clam_unpacker.log
  --trace-file PATH  Override the default trace log file
  -v, --verbose      Enable verbose logging
  -q, --quiet        Disable all logging
  --help             Show this message and exit.

Commands:
  cleanup
  deepscan
  unpack

```
##### COMMANDS
* cleanup - This command will clean up the temp directories/files created as part of the script to scan input file/Dir.
```
Usage: main.py cleanup [OPTIONS] PATH

Options:
  --file          Recursively cleanup directories associated with the file
  --tmp-dir PATH  Directory to search for unpacked files(default: /tmp)
  --help          Show this message and exit.

```

* deepscan - This command is used to scan PATH (**Regular files/Directories**). 
This command runs in three parts, ***"unpack" "scan" "cleanup"***. User can set up certain options to change the behaviour of the command.  
```
Usage: main.py deepscan [OPTIONS] PATH

Options:
  --min-size TEXT   Minimum file size to unpack (default: 2.0 GiB)
  --ignore-size     Ignore file size lower limit (equivalent to --min-size=0)
  --tmp-dir PATH    Temporary working directory (default: /tmp)
  -ff, --fail-fast  Stop scanning after the first failure
  --allmatch        Stop scanning after the first failure
  --help            Show this message and exit.

```
* unpack - This command unpack/mount the input file recursively depending on filetype and store them in a tmp directory 
for recursive scan.
```
Usage: main.py unpack [OPTIONS] PATH

Options:
  -r, --recursive  Recursively unpack files
  --min-size TEXT  Minimum file size to unpack (default: 2.0 GiB)
  --ignore-size    Ignore file size lower limit (equivalent to --min-size=0)
  --tmp-dir PATH   Directory to unpack files to (default: /tmp)
  --help           Show this message and exit.

```

## Examples
Scan command
```
python3 main.py -t -v deepscan <input-archive>
```

unpack command 
```
python3 main.py -t -v unpack <input-archive>
```

## Contributing
[There are many ways to contribute](CONTRIBUTING.md).

## License
This project is licensed under [the BSD 3-Clause license](LICENSE).