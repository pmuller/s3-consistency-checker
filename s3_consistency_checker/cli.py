"""Command line tool.
"""
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
import logging
import sys

from s3_consistency_checker.comparison import compare, ComparisonFailed
from s3_consistency_checker.s3.etag import S3EtagComputer
from s3_consistency_checker.s3.url import S3URL
from s3_consistency_checker.utils import find_files, human_readable_bytes
from s3_consistency_checker import shm


LOGGER = logging.getLogger(__name__)
DEFAULT_MESSAGE_FORMAT = '%(asctime)s.%(msecs)03d %(levelname)s %(message)s'
DEFAULT_DATE_FORMAT = '%Y/%m/%d %H:%M:%S'


def parse_arguments():
    """Parse command line arguments.
    """
    parser = ArgumentParser()

    parser.add_argument('--debug', '-D', default=False, action='store_true')
    parser.add_argument(
        '--s3-chunk-size', metavar='N', default=8 * 1024 * 1024,
        help='Default: %(default)s')
    parser.add_argument(
        '--file-comparison-workers', '-F', metavar='N', default=32, type=int,
        help='File comparison workers. Default: %(default)s')
    parser.add_argument(
        '--md5-workers', '-M', metavar='N', default=64, type=int,
        help='MD5 computation workers. Default: %(default)s')
    parser.add_argument(
        '--max-shm-allocation', '-S', metavar='N', type=int,
        help='Maximum allocation of /dev/shm in bytes. '
             'Default: use all available space.')
    parser.add_argument('local_dir')
    parser.add_argument('s3_url', type=S3URL.parse)

    return parser.parse_args()


def configure_logging(debug=False,
                      message_format=DEFAULT_MESSAGE_FORMAT,
                      date_format=DEFAULT_DATE_FORMAT,
                      stream=sys.stdout):
    """Configure logging.
    """
    level = logging.DEBUG if debug else logging.INFO
    formatter = logging.Formatter(message_format, date_format)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
    logging.getLogger('botocore').setLevel(logging.WARNING)


def main():
    """Main command line entry point.
    """
    arguments = parse_arguments()

    configure_logging(arguments.debug)

    file_comparison_executor = ThreadPoolExecutor(
        arguments.file_comparison_workers)
    s3_etag_compute = S3EtagComputer(
        arguments.s3_chunk_size,
        ThreadPoolExecutor(arguments.md5_workers),
        shm.Allocator(arguments.max_shm_allocation))

    files = [
        filepath.replace(arguments.local_dir, '')
        for filepath in find_files(arguments.local_dir)]
    file_count = len(files)

    LOGGER.info(
        'Comparing %s files from %s with %s',
        file_count, arguments.local_dir, arguments.s3_url)
    LOGGER.debug(
        'File comparison workers: %s', arguments.file_comparison_workers)

    jobs = {}

    for filepath in files:
        jobs[filepath] = file_comparison_executor.submit(
            compare, filepath, arguments.local_dir, s3_etag_compute,
            arguments.s3_url.bucket, arguments.s3_url.prefix)

    errors = 0
    total_bytes = 0

    for filepath, job in jobs.items():
        LOGGER.debug('Waiting for comparison: %s', filepath)

        try:
            total_bytes += job.result()
        except ComparisonFailed as error:
            LOGGER.critical(str(error))
            errors += 1

    LOGGER.info('success=%s errors=%s files=%s bytes=%s',
                file_count - errors, errors, file_count,
                human_readable_bytes(total_bytes))

    if errors:
        sys.exit(-1)
