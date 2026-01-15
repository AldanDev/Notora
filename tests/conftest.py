def pytest_addoption(parser) -> None:  # type: ignore[no-untyped-def]
    parser.addoption('--postgres-version', action='store', default='latest')
