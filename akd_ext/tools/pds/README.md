# PDS Tools

Tools for querying NASA Planetary Data System (PDS) APIs and archives, grouped by node/service:
`img` (Imaging Atlas), `ode` (Orbital Data Explorer), `opus` (Outer Planets), `pds4` (PDS4 registry),
`pds_catalog` (local scraped catalog), `sbn` (Small Bodies Node).

## Result limits

Search/list tools accept a `limit` (or `rows`) parameter, capped by a hard maximum enforced via the
Pydantic field (`le=...`) and, where noted, re-clamped at runtime. Caps are kept small to avoid
overwhelming LLM context windows. Every capped tool's docstring states its cap and, in the
"Pagination" column below, how to get more results when the response signals there are more
(`total_hits`/`num_found`/`available`/`has_more` exceeding what was returned):

- **paginate** — the API supports a page/offset param; use it to fetch subsequent pages instead of raising `limit`
- **narrow query** — the API has no offset support; the only way to see more is a more specific query (keywords, filters, time range, etc.)

Tools without a `limit` row return either a single record or a scalar count, so no result-size cap applies.

| Tool | File | Default | Max | Pagination | Notes |
|---|---|---|---|---|---|
| `img_search_tool` | `img/search.py` | 10 | **10** | paginate via `start` | param name is `rows`, not `limit` |
| `img_get_facets_tool` | `img/get_facets.py` | 10 | 25 | narrow query (`target`/`mission`/`instrument`) | lightweight value/count pairs, sorted by count desc |
| `img_count_tool` | `img/count.py` | — | — | — | returns a count only |
| `img_get_product_tool` | `img/get_product.py` | — | — | — | single product lookup |
| `ode_search_products_tool` | `ode/search_products.py` | 10 | 10 | paginate via `offset` (`has_more` flag) | |
| `ode_list_instruments_tool` | `ode/list_instruments.py` | 25 | 25 | narrow query | |
| `ode_list_feature_names_tool` | `ode/list_feature_names.py` | 25 | 25 | narrow query | |
| `ode_list_feature_classes_tool` | `ode/list_feature_classes.py` | — | — | — | fixed enumeration |
| `ode_count_products_tool` | `ode/count_products.py` | — | — | — | returns a count only |
| `ode_get_feature_bounds_tool` | `ode/get_feature_bounds.py` | — | — | — | single feature lookup |
| `opus_search_tool` | `opus/opus_search.py` | 10 | **15** | paginate via `startobs` | |
| `opus_count_tool` | `opus/opus_count.py` | — | — | — | returns a count only |
| `opus_get_files_tool` | `opus/opus_get_files.py` | — | — | — | single observation lookup |
| `opus_get_metadata_tool` | `opus/opus_get_metadata.py` | — | — | — | single observation lookup |
| `pds4search_products_tool` | `pds4/search_products.py` | 10 | **10** | narrow query | heaviest per-record payload; no offset support in PDS4 API |
| `pds4search_bundles_tool` | `pds4/search_bundles.py` | 10 | **10** | narrow query | `limit=0` = facets-only mode; `facet_limit` max 25 |
| `pds4search_collections_tool` | `pds4/search_collections.py` | 10 | **15** | narrow query | |
| `pds4search_investigations_tool` | `pds4/search_investigations.py` | 10 | 25 | narrow query | light record |
| `pds4search_targets_tool` | `pds4/search_targets.py` | 10 | 25 | narrow query | light record |
| `pds4search_instruments_tool` | `pds4/search_instruments.py` | 10 | 25 | narrow query | light record |
| `pds4search_instrument_hosts_tool` | `pds4/search_instrument_hosts.py` | 10 | 25 | narrow query | light record |
| `pds4get_product_tool` | `pds4/get_product.py` | — | — | — | single product lookup |
| `pds4crawl_context_product_tool` | `pds4/crawl_context_product.py` | — | — | — | fixed set of related products |
| `pds_catalog_search_tool` | `pds_catalog/search.py` | **10** | **20** | paginate via `offset` (`has_more` flag) | was default 20 / max 50; `fields="full"` can be heavy |
| `pds_catalog_list_missions_tool` | `pds_catalog/list_missions.py` | **30** | **30** | narrow query (`node` filter); `has_more`/`total_available` in response | was 50, no offset support |
| `pds_catalog_list_targets_tool` | `pds_catalog/list_targets.py` | **30** | **30** | narrow query (`node` filter); `has_more`/`total_available` in response | was 50, no offset support |
| `pds_catalog_get_dataset_tool` | `pds_catalog/get_dataset.py` | — | — | — | single dataset lookup |
| `pds_catalog_stats_tool` | `pds_catalog/stats.py` | — | — | — | fixed-shape aggregate stats |
| `sbn_search_object_tool` | `sbn/search_object.py` | 10 | 10 | paginate via `offset` (`has_more` flag) | |
| `sbn_search_coordinates_tool` | `sbn/search_coordinates.py` | 10 | 10 | paginate via `offset` (`has_more` flag) | |
| `sbn_list_sources_tool` | `sbn/list_sources.py` | — | — | — | fixed enumeration |

Bold values mark caps tightened in the last context-overflow pass; everything else already had a
sane cap (or intentionally keeps a higher cap for tools returning light records where browsing many
keyword matches is the main use case) and was left as-is.

`pds_catalog_list_missions_tool`/`list_targets_tool` responses include `total_available` (count
before truncation) and `has_more` so the orchestrator can tell when the cap was hit, even though
there's no way to page past it other than narrowing with `node`.
