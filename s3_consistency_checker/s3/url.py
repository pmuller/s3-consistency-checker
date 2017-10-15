from collections import namedtuple
import urllib.parse


BaseS3URL = namedtuple('BaseS3URL', ('bucket', 'prefix'))


class S3URL(BaseS3URL):
    """Parse and represent a S3 URL.
    """

    @classmethod
    def parse(cls, string):
        """Parse an URL.

        >>> assert S3URL.parse('s3://foo').bucket == 'foo'
        >>> assert S3URL.parse('s3://foo').prefix == ''
        >>> assert S3URL.parse('s3://foo/').prefix == ''
        >>> assert S3URL.parse('s3://foo/bar').prefix == 'bar'

        """
        parsed = urllib.parse.urlparse(string)

        if parsed.scheme != 's3':
            raise ValueError(
                'Invalid scheme: %r (must be "s3")' % parsed.scheme)
        elif parsed.netloc == '':
            raise ValueError('S3 bucket name undefined')

        prefix = parsed.path

        if prefix and prefix[0] == '/':
            prefix = prefix[1:]

        return cls(parsed.netloc, prefix)

    def __str__(self):
        """String representation.

        >>> assert str(S3URL('foo', 'bar')) == 's3://foo/bar'

        """
        return 's3://%s/%s' % (self.bucket, self.prefix)
