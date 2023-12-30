from pathlib import Path
import logging
import argparse
from textwrap import dedent

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=dedent('''
    Synchronizes two folders: source and replica. 
    The program maintains a full, identical copy of 
    source folder at replica folder                   
    ''')
)

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

args = parser.parse_args(['-v', 'source_path', 'replica_path',
                          '60', 'sync_file.log'])

print(args)

#  Set logger
logger = logging.getLogger(__name__)
logger.setLevel(args.loglevel)

#  Define Stream Handler
logs_fmt_str_02 = '%(asctime)-19.19s %(levelname)-7.7s %(name)s@' \
                  '%(funcName)s %(message)s'
logs_fmt_02 = logging.Formatter(logs_fmt_str_02)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(args.loglevel)
stream_handler.setFormatter(logs_fmt_02)
logger.addHandler(stream_handler)

#  Define File Handler
file_handler = logging.FileHandler(args.log_file)
file_handler.setLevel(logging.INFO)
logs_fmt_str_01 = '%(levelname)-5.5s %(name)s@%(funcName)s %(message)s'  # TODO  delete
logs_fmt_01 = logging.Formatter(logs_fmt_str_01)  # TODO  delete
file_handler.setFormatter(logs_fmt_02)
logger.addHandler(file_handler)

logger.info('Test 001')
logger.warning('Test 002')

source_dir = args.source_dir
replica_dir = args.replica_dir

logger.debug(f'{source_dir=} and {replica_dir=}')
logger.debug(f'{source_dir.resolve()=}')
logger.debug(f'{replica_dir.resolve()=}')
