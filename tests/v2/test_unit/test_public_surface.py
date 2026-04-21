import notora.v2 as n2


def test_top_level_reexports_exist() -> None:
    expected = {
        # repo
        'Repository',
        'SoftDeleteRepository',
        'RepoConfig',
        'QueryParams',
        'PaginationParams',
        'FilterSpec',
        'OrderSpec',
        'FilterClause',
        'OrderClause',
        'FilterField',
        'SortField',
        'QueryInput',
        'build_query_params',
        'make_query_params_dependency',
        'apply_filter_operator',
        # service
        'RepositoryService',
        'SoftDeleteRepositoryService',
        'ServiceConfig',
        # schemas
        'BaseRequestSchema',
        'BaseResponseSchema',
        'PaginatedResponseSchema',
        'PaginationMetaSchema',
        'PydanticFilterField',
        'PydanticFiltersSchema',
        'PydanticOrderBySchema',
        'PydanticSortField',
        # fastapi
        'make_list_params_dependency',
    }
    missing = {name for name in expected if not hasattr(n2, name)}
    assert missing == set(), f'missing reexports: {sorted(missing)}'
