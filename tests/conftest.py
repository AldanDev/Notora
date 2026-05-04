import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption('--postgres-version', action='store', default='latest')
