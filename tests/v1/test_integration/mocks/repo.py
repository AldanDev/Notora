from uuid import UUID

from notora.v1.persistence.repos.base import SoftDeletableRepo
from tests.v1.test_integration.mocks.model import MockModel


class MockRepo(SoftDeletableRepo[UUID, MockModel]): ...
