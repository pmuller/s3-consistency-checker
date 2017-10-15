import logging
from os import statvfs
from threading import Lock

from s3_consistency_checker.utils import human_readable_bytes


LOGGER = logging.getLogger(__name__)


class Overflow(Exception):
    """Raised when trying to allocate too much memory from /dev/shm.
    """

    def __init__(self, allocator, add_value):
        self.allocator = allocator
        self.add_value = add_value
        super().__init__(
            'Failed to allocate %s from /dev/shm (free: %s)' % (
                human_readable_bytes(add_value),
                human_readable_bytes(self.allocator.available)))


class Allocator:
    """Thread-safe /dev/shm allocator.
    """

    def __init__(self, max_allocation=None, lock=None):
        if max_allocation is None:
            shm_stat = statvfs('/dev/shm')
            self.max_allocation = shm_stat.f_frsize * shm_stat.f_ffree
        else:
            self.max_allocation = max_allocation

        self.allocated = 0
        self.lock = lock or Lock()

        LOGGER.debug(
            'SHM allocator initialized: max_allocation=%s',
            human_readable_bytes(self.max_allocation))

    def allocate(self, value):
        """Allocate bytes from /dev/shm.
        """
        with self.lock:
            if self.allocated + value > self.max_allocation:
                raise Overflow(self, value)

            self.allocated += value

        LOGGER.debug('Allocated %s from /dev/shm (free: %s)',
                     human_readable_bytes(value),
                     human_readable_bytes(self.available))

    def free(self, value):
        """Free bytes from /dev/shm.
        """
        with self.lock:
            self.allocated = max(self.allocated - value, 0)

        LOGGER.debug('Freed %s from /dev/shm (free: %s)',
                     human_readable_bytes(value),
                     human_readable_bytes(self.available))

    @property
    def available(self):
        """Return the amount of available bytes in /dev/shm.
        """
        return self.max_allocation - self.allocated
