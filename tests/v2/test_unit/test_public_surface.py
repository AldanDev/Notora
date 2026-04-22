import notora.v2 as n2


def test_top_level_surface_matches_expected() -> None:
    expected = {
        # repo
        'Repository',
        'SoftDeleteRepository',
        'RepoConfig',
        'QueryParams',
        'PaginationParams',
        'FilterSpec',
        'FilterFactory',
        'OrderSpec',
        'OrderFactory',
        'OptionSpec',
        'OptionFactory',
        'FilterClause',
        'OrderClause',
        'FilterField',
        'SortField',
        'QueryInput',
        'build_query_params',
        'make_query_params_dependency',
        'apply_filter_operator',
        'resolve_to_column',
        # service
        'RepositoryService',
        'SoftDeleteRepositoryService',
        'ServiceConfig',
        # schemas
        'BaseRequestSchema',
        'BaseResponseSchema',
        'ClientMeta',
        'PaginatedResponseSchema',
        'PaginationMetaSchema',
        'PydanticFilterField',
        'PydanticFiltersSchema',
        'PydanticOrderBySchema',
        'PydanticSortField',
        # fastapi
        'make_list_params_dependency',
    }
    actual = set(n2.__all__)
    missing = expected - actual
    extras = actual - expected
    assert missing == set(), f'missing reexports: {sorted(missing)}'
    assert extras == set(), f'unexpected reexports in __all__: {sorted(extras)}'
    # Also verify that every name in __all__ is actually defined on the module
    unreachable = {name for name in n2.__all__ if not hasattr(n2, name)}
    assert unreachable == set(), f'names in __all__ but not on module: {sorted(unreachable)}'
