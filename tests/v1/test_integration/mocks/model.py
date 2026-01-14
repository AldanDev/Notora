from sqlalchemy.orm import Mapped

from notora.v1.models.base import BaseModel
from tests.v1.factories.base import SQLAlchemyBaseModelFactory


class User(BaseModel): ...


class MockModel(BaseModel):
    name: Mapped[str]


class MockModelFactory(SQLAlchemyBaseModelFactory[MockModel]): ...
