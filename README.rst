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

    $ time s3-consistency-checker /path/to/local/data bucket-name optional-s3-prefix
    INFO:__main__:Comparing 2076 files from /path/to/local/data with s3://bucket-name/optional-s3-prefix


Installation
------------

.. code-block:: console

    $ pip install s3-consistency-checker


Requirements
------------

* Python 3.x
* boto3
* Command line tools: md5sum, split
