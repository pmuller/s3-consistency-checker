"""Computation of S3 ETags.
"""
from hashlib import md5
from os import listdir
from shutil import rmtree
from subprocess import Popen, PIPE
from tempfile import mkdtemp


def run(command, **kwargs):
    """Run ``command``.
    """
    command = command.split() if isinstance(command, str) else command
    process = Popen(command, stdout=PIPE, stderr=PIPE, **kwargs)
    stdout, stderr = process.communicate()
    assert process.returncode == 0
    return stdout, stderr


def md5sum(filepath):
    """Get the MD5 checksum of ``filepath``.
    """
    return run('md5sum %s' % filepath)[0].split()[0]


def compute(filepath, chunk_size, executor):
    """Compute the S3 ETag of ``filepath``.
    """
    tmp_dir = mkdtemp(prefix='/dev/shm/')

    try:
        run('split --bytes=%s %s %s/' % (chunk_size, filepath, tmp_dir))
        parts = listdir(tmp_dir)
        chunk_count = len(parts)
        files = ['%s/%s' % (tmp_dir, filename) for filename in sorted(parts)]
        checksums = list(executor.map(md5sum, files))
    finally:
        rmtree(tmp_dir)

    if chunk_count == 1:
        return checksums[0].decode('ascii')
    else:
        bytes_checksums = bytearray.fromhex(
            b''.join(checksums).decode('ascii'))
        return '%s-%s' % (md5(bytes_checksums).hexdigest(), chunk_count)
