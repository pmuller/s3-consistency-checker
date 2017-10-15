from os.path import join, dirname, abspath

from setuptools import setup, find_packages


def read(filename):
    with open(abspath(join(dirname(__file__), filename))) as fileobj:
        return fileobj.read()


def get_version(package):
    return [
        line for line in read('{}/__init__.py'.format(package)).splitlines()
        if line.startswith('__version__ = ')][0].split("'")[1]


NAME = 's3-consistency-checker'
PACKAGE = NAME.replace('-', '_')
VERSION = get_version(PACKAGE)


setup(
    name=NAME,
    version=VERSION,
    description='Check consistency of files stored on S3 against local files',
    long_description=read('README.rst'),
    packages=find_packages(exclude=['dev']),
    author='Philippe Muller',
    author_email='philippe.muller@gmail.com',
    install_requires=[
        'boto3 >=1.4.7',
    ],
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3.5',
        'Intended Audience :: Developers',
        'Development Status :: 5 - Production/Stable',
        'Operating System :: POSIX :: Linux',
    ],
    keywords='s3',
    url='https://github.com/pmuller/s3-consistency-checker',
    license='Apache License 2.0',
    entry_points="""
        [console_scripts]
        s3-consistency-checker = s3_consistency_checker.cli:main
    """,
)
