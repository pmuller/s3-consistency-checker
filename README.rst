S3 consistency checker
======================

``aws s3 sync`` is great!

But if you are truly paranoid about your precious files safety,
it's always better to double check what was uploaded to S3 before deleting
them from your local file system.

This tool does exactly that:

#. List recursively your local files
#. Ask S3 for their sizes and ETags
#. Check this against locally computed ETags


Usage
-----

.. code-block:: console

    $ time s3-consistency-checker /data/foo bucketname foo
    2017/10/14 16:30:58.729 INFO Comparing 2093 files from /data//foo with s3://bucketname/foo
    2017/10/14 17:43:18.222 INFO success=2093 errors=0 files=2093 bytes=1.3TiB

    real    72m20.097s
    user    55m6.975s
    sys     778m45.112s

    $ time s3-consistency-checker /data/bar bucketname baz
    2017/10/14 18:47:08.620 INFO Comparing 26531 files from /data/bar with s3://bucketname/baz
    2017/10/14 19:21:48.425 INFO success=26531 errors=0 files=26531 bytes=220.1GiB

    real    34m42.023s
    user    40m22.292s
    sys     33m57.729s

    $ time s3-consistency-checker /data/foobar bucketname foobar
    2017/10/15 02:11:00.904 INFO Comparing 11224 files from /data/foobar with s3://bucketname/foobar
    2017/10/15 02:25:18.397 INFO success=11224 errors=0 files=11224 bytes=84.8GiB

    real    14m18.873s
    user    17m3.899s
    sys     10m33.841s


Internals
---------

This tool is designed to process a lot of big files as quickly as possible.
It uses the ``split`` command to split big files in chunks,
stores them in ``/dev/shm``,
then computes their checksums using the ``md5sum`` command.
It does this in parallel using separate processes and threads to drive them.


Installation
------------

.. code-block:: console

    $ pip install s3-consistency-checker


Requirements
------------

* Python 3.x
* boto3
* coreutils: md5sum, split
