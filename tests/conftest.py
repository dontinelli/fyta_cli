"""Tests for fyta_cli - configurations."""

from typing import Generator

from aioresponses import aioresponses
import pytest

from syrupy import SnapshotAssertion

from .syrupy import FytaSnapshotExtension


@pytest.fixture(name="snapshot")
def snapshot_assertion(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Fyta extension."""
    return snapshot.use_extension(FytaSnapshotExtension)

@pytest.fixture(name="responses")
def aioresponses_fixture() -> Generator[aioresponses, None, None]:
    """Return aioresponses fixture."""
    with aioresponses() as mocked_responses:
        yield mocked_responses
