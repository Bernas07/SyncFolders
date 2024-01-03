#!/bin/python

import os
from pathlib import Path
import filecmp
import shutil
import argparse
import logging
import time
from textwrap import dedent

logger = logging.getLogger(__name__)


def Parse_Args(parser: argparse.ArgumentParser):
    """
    Add the arguments to the ArgumentParser.
    """
    parser.add_argument('-v', '--verbose', dest='loglevel',
                        action='store_const', const=logging.DEBUG,
                        default=logging.INFO,
                        help='Add more details to the standard error log')
    parser.add_argument('source_dir', type=Path,
                        help='Source directory for synchronization')
    parser.add_argument('replica_dir', type=Path,
                        help='Replica directory for synchronization')
    parser.add_argument('sync_interval', type=float,
                        help='Synchronization interval time in second unit')
    parser.add_argument('log_file', type=Path,
                        help='Log file path')


def get_abspath(directory_p: Path) -> Path:
    '''
    Parses input directory. Checks for symlinks and relative paths
    Returns real absolute Path
    '''
    directory_p = directory_p.absolute()
    if directory_p.is_symlink():
        dir_points_to = directory_p.readlink()
        if not dir_points_to.is_absolute():
            directory_p = directory_p.parent / dir_points_to
        else:
            directory_p = dir_points_to
    return directory_p


def check_if_dir_and_not_sym(p: Path) -> bool:
    """
    Filter real directories paths, not symlinks
    """
    return p.is_dir() and not p.is_symlink()


def iter_dir(directory: Path, path_set=None, base_dir=None) -> set:
    """
    Parses tree directory and returns a set will all the
    files path in the hierarchy
    """
    if path_set is None or base_dir is None:
        base_dir = directory
        path_set = set()
    for p in directory.iterdir():
        if check_if_dir_and_not_sym(p):
            iter_dir(p, path_set, base_dir)
        path_set.add(p.relative_to(base_dir))
    return path_set


def sort_paths_set_by_sep(paths_set: set, reverse=False) -> tuple:
    """
    Sorts the file's path in the set paths_set parameter according to
    the number of os.sep(). Parents files will appear before child files,
    according to sort's orientation.
    """
    return tuple(sorted(paths_set,
                        key=lambda p: str(p).count(os.sep),
                        reverse=reverse)
                        )


def rm_files_in_set(base_dir, set_paths: set):
    """
    Removes all files in set_paths from base dir
    """
    set_paths_sorted = sort_paths_set_by_sep(set_paths, reverse=True)
    for p in set_paths_sorted:
        full_path = base_dir / p
        if check_if_dir_and_not_sym(full_path):
            logger.info('Removing directory: %s', full_path)
            try:
                full_path.rmdir()
            except Exception:
                logger.error('Failed to remove directory: %s', full_path)
                raise
        elif full_path.is_symlink():
            logger.info('Removing symlink: %s -> %s',
                        full_path,
                        full_path.readlink()
                        )
            try:
                full_path.unlink()
            except Exception:
                logger.error('Failed to delete symlink: %s', full_path)
                raise
        else:
            logger.info('Removing file: %s', full_path)
            try:
                full_path.unlink()
            except Exception:
                logger.error('Failed to delete symlink: %s', full_path)
                raise


def main():
    """
    Main function
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent('''
        Synchronizes two folders: source and replica.
        The program maintains a full, identical copy of
        source folder at replica folder
        ''')
    )

    Parse_Args(parser)
    args = parser.parse_args()

    #  Config logger
    logger.setLevel(args.loglevel)
    logs_fmt_str = '%(asctime)-19.19s %(levelname)-7.7s %(name)s@' \
                   '%(funcName)s %(message)s'
    logs_fmt = logging.Formatter(logs_fmt_str)

    #  Define Stream Handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(args.loglevel)
    stream_handler.setFormatter(logs_fmt)
    logger.addHandler(stream_handler)

    #  Define File Handler
    file_handler = logging.FileHandler(args.log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logs_fmt)
    logger.addHandler(file_handler)

    source_dir = args.source_dir
    replica_dir = args.replica_dir

    if not source_dir.exists():
        logger.error('Input source directory: "%s" does not exist.',
                     source_dir)
        raise FileExistsError('Source directory does not exist')

    if not source_dir.is_dir():
        logger.error('Input source directory "%s" is not a valid directory',
                     source_dir)
        raise FileExistsError('Source directory does not exist')

    source_dir = get_abspath(source_dir)
    logger.debug('Source directory is: %s', source_dir)

    replica_dir = get_abspath(replica_dir)
    logger.debug('Replica directory is: %s', replica_dir)

    while True:
        updated = False
        logger.debug('Checking directories synchronization')

        #  Source directory set with relative file's path
        src_rel_paths = iter_dir(source_dir)

        #  Copies hierarchically source directory to replica directory
        #  in case that target directory has not been created yet
        if not replica_dir.exists():
            updated = True
            src_rel_paths_sorted = sort_paths_set_by_sep(src_rel_paths)
            logger.info('Creating directory: %s', replica_dir)
            try:
                shutil.copytree(source_dir, replica_dir, symlinks=True)
            except Exception:
                logger.error('Failed to create replica directory: %s',
                             replica_dir)
                raise
            for p in src_rel_paths_sorted:
                src_full_path = source_dir / p
                rep_full_path = replica_dir / p
                if check_if_dir_and_not_sym(src_full_path):
                    logger.info('Creating directory: %s', rep_full_path)
                elif src_full_path.is_symlink():
                    logger.info('Creating symlink: %s -> %s',
                                rep_full_path,
                                src_full_path.readlink())
                else:
                    logger.info('Creating file: %s', rep_full_path)
            time.sleep(args.sync_interval)
            continue

        #  Replica directory set with relative file's path
        rep_rel_paths = iter_dir(replica_dir)

        only_in_rep = rep_rel_paths - src_rel_paths
        only_in_src = src_rel_paths - rep_rel_paths

        #  Delete files that only exist in replica
        if len(only_in_rep):
            updated = True
            logger.debug('Files only in replica directory: %s', only_in_rep)
            rm_files_in_set(replica_dir, only_in_rep)

        #  Check common files
        common_rel_paths = src_rel_paths.intersection(rep_rel_paths)

        if len(common_rel_paths) > 0:
            for p in common_rel_paths:
                src_path = source_dir / p
                rep_path = replica_dir / p

                if check_if_dir_and_not_sym(src_path):
                    continue

                if src_path.is_symlink():
                    if not src_path.readlink() == rep_path.readlink():
                        updated = True
                        rep_path.unlink()
                        logger.info('Updating symlink: %s -> %s', rep_path,
                                    src_path.readlink())
                        try:
                            shutil.copy2(src_path, rep_path,
                                         follow_symlinks=False)
                        except Exception:
                            logger.error('Failed to create symlink: %s -> %s',
                                         rep_path, src_path.readlink())
                            raise
                else:
                    if not filecmp.cmp(src_path, rep_path):
                        updated = True
                        logger.info('Updating file: %s', rep_path)
                        try:
                            shutil.copy2(src_path, rep_path,
                                         follow_symlinks=False)
                        except Exception:
                            logger.error('Failed to update file: %s', rep_path)
                            raise

        #  Copy files only in source directory to replica directory
        if len(only_in_src) > 0:
            updated = True
            logger.debug('Files only in source directory: %s', only_in_src)

            #  Sorts iterable according to deph in directory tree,
            #  so it will create parent directories before its child files
            only_in_src_sorted = sort_paths_set_by_sep(only_in_src)
            for p in only_in_src_sorted:
                src_path = source_dir / p
                rep_path: Path = replica_dir / p
                if check_if_dir_and_not_sym(src_path):
                    logger.info('Creating directory: %s', rep_path)
                    try:
                        rep_path.mkdir()
                    except Exception:
                        logger.error('Failed to create directory: %s',
                                     rep_path)
                        raise
                    continue
                elif src_path.is_symlink():
                    logger.info('Creating symlink: %s -> %s',
                                rep_path, src_path.readlink())
                else:
                    logger.info('Creating file: %s', rep_path)
                try:
                    shutil.copy2(src_path, rep_path, follow_symlinks=False)
                except Exception:
                    logger.error('Failed to create file/symlink: %s', rep_path)
                    raise
        if not updated:
            logger.debug('Directory: "%s" already synchronized with "%s"',
                         source_dir, replica_dir)
        time.sleep(args.sync_interval)


if __name__ == '__main__':
    main()
