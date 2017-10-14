"""Comparison of files between local file system and S3 bucket.
"""
import logging
from os import stat

from boto3 import Session
from botocore.exceptions import ClientError


LOGGER = logging.getLogger(__name__)


class ComparisonFailed(Exception):
    """Raised when a file comparison fails.
    """

    def __init__(self, error, filepath, local=None, remote=None):
        self.error = error
        self.filepath = filepath
        self.local = local
        self.remote = remote

        message = 'Comparison failed for %s: %s' % (filepath, error)
        if local and remote:
            message += ' (local=%s remote=%s)' % (local, remote)

        super().__init__(message)


def add_prefix(string, prefix=None):
    """Add ``prefix`` to ``string``, if not ``None``.
    """
    return string if prefix is None else '%s%s' % (prefix, string)


def compare(  # pylint: disable=too-many-arguments
        filepath, local_prefix, s3_etag_compute, s3_bucket,
        s3_prefix=None, s3_client=None):
    """Compare a file' size and etag between a local and a S3 copy.
    """
    LOGGER.debug('Comparing %s', filepath)
    s3_path = add_prefix(filepath, s3_prefix)
    s3_client = s3_client or Session().client('s3')

    try:
        s3_metadata = s3_client.head_object(Key=s3_path, Bucket=s3_bucket)
    except ClientError as error:
        raise ComparisonFailed(
            'Cannot retrieve S3 metadata: %s' % error, filepath)

    local_path = add_prefix(filepath, local_prefix)
    size = stat(local_path).st_size
    remote_etag = s3_metadata['ETag'].replace('"', '')

    if size != s3_metadata['ContentLength']:
        raise ComparisonFailed(
            'different size', filepath, size, s3_metadata['ContentLength'])

    local_etag = s3_etag_compute(local_path, size)

    if local_etag != remote_etag:
        raise ComparisonFailed(
            'different etag', filepath, local_etag, remote_etag)

    LOGGER.debug('Comparison successful: %s', filepath)

    return size
