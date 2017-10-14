from os import walk
from os.path import join


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
