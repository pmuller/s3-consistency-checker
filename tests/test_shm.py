import pytest

from s3_consistency_checker.shm import Allocator, Overflow


def test_allocator():
    allocator = Allocator(100)
    allocator.allocate(58)
    assert allocator.available == 42
    allocator.free(100000)
    assert allocator.available == 100


def test_allocator_overflow():
    with pytest.raises(Overflow) as overflow:
        Allocator(0).allocate(1)
    assert str(overflow).endswith(
        'Failed to allocate 1.0B from /dev/shm (free: 0.0B)')
