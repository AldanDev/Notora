from uuid import UUID

from notora.persistence.repos.base import SoftDeletableRepo
from tests.test_integration.mocks.model import MockModel


class MockRepo(SoftDeletableRepo[UUID, MockModel]): ...
