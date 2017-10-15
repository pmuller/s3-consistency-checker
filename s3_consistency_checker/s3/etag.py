"""Computation of S3 ETags.
"""
from concurrent.futures import ThreadPoolExecutor
from hashlib import md5
import logging
from os import listdir, stat
from shutil import rmtree
from subprocess import Popen, PIPE
from tempfile import mkdtemp
from time import sleep

from s3_consistency_checker import shm


LOGGER = logging.getLogger(__name__)


def run(command, **kwargs):
    """Run ``command``.
    """
    command = command.split() if isinstance(command, str) else command
    process = Popen(command, stdout=PIPE, stderr=PIPE, **kwargs)
    stdout, stderr = process.communicate()
    assert process.returncode == 0, \
        'Command %r exited with code %s: stdout=%r stderr=%r' % (
            command, process.returncode, stdout, stderr)
    return stdout, stderr


def md5sum(filepath):
    """Get the MD5 checksum of ``filepath``.
    """
    return run('md5sum %s' % filepath)[0].split()[0]


def compute_small(filepath):
    """Compute S3 ETag for a small file, up to 1 chunk size.
    """
    with open(filepath, 'rb') as fileobj:
        return md5(fileobj.read()).hexdigest()


def compute_large(filepath, chunk_size, md5_executor):
    """Compute the S3 ETag of a file bigger than ``chunk_size``.
    """
    tmp_dir = mkdtemp(prefix='/dev/shm/s3-consistency-checker-')

    try:
        run('split --bytes=%s %s %s/' % (chunk_size, filepath, tmp_dir))
        parts = listdir(tmp_dir)
        files = ['%s/%s' % (tmp_dir, filename) for filename in sorted(parts)]
        checksums = list(md5_executor.map(md5sum, files))
    finally:
        rmtree(tmp_dir)

    bytes_checksums = bytearray.fromhex(b''.join(checksums).decode('ascii'))
    return '%s-%s' % (md5(bytes_checksums).hexdigest(), len(parts))


class S3EtagComputer:
    """Compute etags in parallel.

    If ``filepath`` is larger than ``chunk_size``,
    the file will be split in several chunks in ``/dev/shm``,
    and parallel ``md5sum`` processes will be used to compute checksums.

    """

    def __init__(self, chunk_size, md5_executor=None, shm_allocator=None):
        self.chunk_size = chunk_size
        self.md5_executor = md5_executor or ThreadPoolExecutor()
        self.shm_allocator = shm_allocator or shm.Allocator()
        LOGGER.debug('S3 ETag computer initialized: max_workers=%s',
                     # pylint: disable=protected-access
                     self.md5_executor._max_workers)

    def __call__(self, filepath, size=None):
        size = size or stat(filepath).st_size

        # Faster for small files
        if size <= self.chunk_size:
            return compute_small(filepath)

        # Ensure we have enough free space in /dev/shm
        while True:
            try:
                self.shm_allocator.allocate(size)

            except shm.Overflow as overflow:
                LOGGER.debug('%s for %s, sleeping 1s', overflow, filepath)
                sleep(1)

            else:
                try:
                    return compute_large(
                        filepath, self.chunk_size, self.md5_executor)
                finally:
                    self.shm_allocator.free(size)
