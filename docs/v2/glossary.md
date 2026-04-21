# Query Glossary (v2)

Terminology for filtering, ordering, and pagination. Use this to disambiguate the layered types.

## Filter terms

| Term | Kind | Purpose |
|---|---|---|
| `FilterClause` | Type alias | A SQLAlchemy `ColumnElement[bool]` — a raw WHERE clause. |
| `FilterFactory[M]` | Type alias | `Callable[[type[M]], FilterClause]` — lazy clause tied to a model. |
| `FilterSpec[M]` | Type alias | `FilterClause \| FilterFactory[M]` — what repo methods accept in `filters=`. |
| `apply_filter_operator(col, op, value)` | Function | Maps an operator name (`eq`, `gte`, …) to a SQLAlchemy clause. |
| `FilterField[M]` | Dataclass | DSL allowlist entry: resolver + allowed operators + value type. Used with `build_query_params`. |
| `FilterToken` | Dataclass | Parsed `field:op:value` from a DSL query string. |
| `PydanticFilterField[M]` | Dataclass | Pydantic-schema allowlist entry: resolver + predicate + fixed operator. Used with `PydanticFiltersSchema`. |

## Order terms

| Term | Kind | Purpose |
|---|---|---|
| `OrderClause` | Type alias | A SQLAlchemy `ColumnElement[Any] \| UnaryExpression[Any]`. |
| `OrderFactory[M]` | Type alias | `Callable[[type[M]], OrderClause]`. |
| `OrderSpec[M]` | Type alias | `OrderClause \| OrderFactory[M]` — what repo methods accept in `ordering=`. |
| `SortField[M]` | Dataclass | DSL allowlist entry for sorting. |
| `SortToken` | Dataclass | Parsed `±field` from DSL. |
| `PydanticSortField[M]` | Dataclass | Pydantic-schema allowlist entry for sorting. |

## Pagination / parameters

| Term | Kind | Purpose |
|---|---|---|
| `QueryParams[M]` | Dataclass | Bag of filters/ordering/limit/offset for `list_*_params`. Carries `apply_default_filters` for per-call bypass. |
| `PaginationParams[M]` | Dataclass | Same bag plus a concrete `limit` default for `paginate_params`. |
| `QueryInput` | Pydantic | FastAPI DSL query schema (`filter=...`, `sort=...`, `limit`, `offset`). |
| `PydanticFiltersSchema[M]` | Pydantic base | OpenAPI-native query-param filters → `list[FilterSpec[M]]`. |
| `PydanticOrderBySchema[M]` | Pydantic base | OpenAPI-native `order_by` + `direction` → `list[OrderSpec[M]]`. |
| `make_query_params_dependency` | Factory | Build a FastAPI `Depends` for the DSL path. |
| `make_list_params_dependency` | Factory | Build a FastAPI `Depends` for the pydantic path (composes filters + ordering + pagination into one `PaginationParams`). |

## Default filters and the bypass flag

Repositories can carry a `default_filters` tuple that gets merged with per-call filters. `SoftDeleteRepository` adds `deleted_at IS NULL`; other repos can register arbitrary clauses via `RepoConfig.default_filters`.

Every method that accepts filters also accepts `apply_default_filters: bool = True`. Pass `False` to skip the defaults for a single call. Used by admin endpoints that need to see soft-deleted rows.

The flag is also a field on `QueryParams` and `PaginationParams`, so it travels through `list_params` / `paginate_params` automatically.

When `paginate(apply_default_filters=False)` is called, BOTH the data query AND the count query skip the defaults. `meta.total` stays consistent with `len(page.data)`.

## Two paths from HTTP to SQL

### DSL path (gateway APIs, public filtering)

Query: `?filter=age:gte:18&sort=-created_at`

Flow: `QueryInput` → `build_query_params(...)` → `QueryParams[M]` → `service.list_params(session, params)`.

Best when: clients are trusted intermediaries; you want a single flexible endpoint; OpenAPI form generation is not needed.

### Pydantic path (admin UIs, OpenAPI-first)

Query: `?age_gte=18&order_by=created_at&direction=desc`

Flow: a `PydanticFiltersSchema` subclass + a `PydanticOrderBySchema` subclass → `make_list_params_dependency(...)` → FastAPI `Depends` → `PaginationParams[M]` → `service.paginate_params(session, params)`.

Best when: the front-end is an admin panel with auto-generated forms; fields are typed (UUID / Enum / Literal); HTTP 422 on invalid input is preferred over a runtime error.

Both paths produce the same `FilterSpec` / `OrderSpec` types, so service/repo layers are agnostic.

## Footguns (pydantic path)

**Subclass field overrides:** `PydanticOrderBySchema` declares `order_by: str | None = None` on the base class. Every subclass MUST override `order_by` with a `Literal[...]` of its `sort_fields` keys. Otherwise pydantic accepts any string from the URL and the `ValueError('Unsupported sort field …')` fires at runtime, producing an HTTP 500 instead of the cleaner 422 that a `Literal` would have produced at validation time.

Example:

```python
class ThingOrdering(PydanticOrderBySchema[Thing]):
    order_by: Literal['created_at', 'updated_at'] | None = None
    direction: Literal['asc', 'desc'] = 'desc'

    sort_fields: ClassVar[dict[str, PydanticSortField[Any]]] = {
        'created_at': PydanticSortField(resolver=Thing.created_at),
        'updated_at': PydanticSortField(resolver=Thing.updated_at),
    }
```

**Mutable ClassVar dict:** `filter_fields` / `sort_fields` are mutable dicts. If you mutate a subclass's dict AFTER class definition (e.g. `ThingFilters.filter_fields['new'] = ...`), the mutation is scoped to that subclass — but if you've **inherited** without overriding the ClassVar, mutation will leak into the parent's dict. Always assign a fresh dict literal in each subclass body; never rely on inheritance of the mutable default.

Safe:

```python
class ThingFilters(PydanticFiltersSchema[Thing]):
    filter_fields: ClassVar[dict[str, PydanticFilterField[Any]]] = {...}  # new dict per subclass
```

Unsafe (don't do this):

```python
class ThingFilters(PydanticFiltersSchema[Thing]):
    ...  # inherits the empty default from the base
    # Later, somewhere in the codebase:
    # ThingFilters.filter_fields['name'] = PydanticFilterField(...)
    # This mutates the BASE class's dict and leaks to all other subclasses.
```
