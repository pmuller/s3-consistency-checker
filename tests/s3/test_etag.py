import pytest

from s3_consistency_checker.s3.etag import run, S3EtagComputer


# Default value from awscli
CHUNK_SIZE = 8 * 1024 * 1024


@pytest.mark.parametrize('chunk_count, etag', (
    (1, '96995b58d4cbf6aaa9041b4f00c7f6ae'),
    (2, '3a2d20e2e504fe056bbaae5b4c2351fd-2'),
))
def test_s3_etag_computer__small(chunk_count, etag, tmpdir):
    filepath = str(tmpdir.join('file'))
    run('dd if=/dev/zero of=%s count=%s bs=%s' % (
        filepath, chunk_count, CHUNK_SIZE))
    assert S3EtagComputer(CHUNK_SIZE)(filepath) == etag
