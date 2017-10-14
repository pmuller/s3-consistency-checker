"""Command line tool.
"""
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
import logging
from os import walk
from os.path import join
import sys


from s3_consistency_checker.comparison import compare, ComparisonFailed


LOGGER = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments.
    """
    parser = ArgumentParser()

    parser.add_argument('--debug', '-D', default=False, action='store_true')
    parser.add_argument(
        '--s3-chunk-size', metavar='N', default=8 * 1024 * 1024,
        help='Default: %(default)s')
    parser.add_argument(
        '--file-comparison-workers', metavar='N', default=32, type=int,
        help='File comparison workers. Default: %(default)s')
    parser.add_argument(
        '--md5-workers', metavar='N', default=64, type=int,
        help='MD5 computation workers. Default: %(default)s')
    parser.add_argument('base_dir')
    parser.add_argument('s3_bucket')
    parser.add_argument('s3_prefix', nargs='?')

    return parser.parse_args()


def find_files(base_dir):
    """Return the list of all files in ``base_dir``, resursively.
    """
    return [
        filepath for sublist in [
            [join(parent_dir, filename) for filename in filenames]
            for parent_dir, _, filenames in walk(base_dir)
        ] for filepath in sublist]


def human_readable_bytes(num, suffix='B'):
    """Convert ``num`` bytes to a human readable string.
    """
    # Source: https://web.archive.org/web/20111010015624/ \
    # http://blogmag.net/blog/read/38/Print_human_readable_file_size
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0

    return "%.1f%s%s" % (num, 'Yi', suffix)


def main():
    """Main command line entry point.
    """
    arguments = parse_arguments()

    logging.basicConfig(
        level=logging.DEBUG if arguments.debug else logging.INFO)
    logging.getLogger('botocore').setLevel(logging.WARNING)

    file_comparison_executor = ThreadPoolExecutor(
        arguments.file_comparison_workers)
    md5_executor = ThreadPoolExecutor(arguments.md5_workers)

    files = [
        filepath.replace(arguments.base_dir, '')
        for filepath in find_files(arguments.base_dir)]
    file_count = len(files)

    LOGGER.info('Comparing %s files from %s with s3://%s/%s',
                file_count, arguments.base_dir, arguments.s3_bucket,
                arguments.s3_prefix or '')

    jobs = {}

    for filepath in files:
        jobs[filepath] = file_comparison_executor.submit(
            compare, filepath, md5_executor, arguments.base_dir,
            arguments.s3_bucket, arguments.s3_chunk_size, arguments.s3_prefix)

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
