from uuid import UUID

from notora.v1.services.base import SoftDeletableService
from tests.v1.test_integration.mocks.model import MockModel
from tests.v1.test_integration.mocks.schema import MockModelResponseSchema


class MockService(SoftDeletableService[UUID, MockModel, MockModelResponseSchema]): ...
