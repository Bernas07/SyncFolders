# SyncFolders
The script was developped using python3.9 on linux.

Please run:
```sh
./main.py -h
```
To see the scrip usage.

The source and replica directories may be given as relative or absolute paths.
Also supports symlinks.

### Example
Synchronize source folder `src_dir_path` to `rep_dir_path` with an interval of `30s` and log it to file `log_file.log`.
Optional '-v' for verbosity (sets logger level to `debug`).
```sh
./main.py src_dir_path rep_dir_path 30 log_file.log -v
```
