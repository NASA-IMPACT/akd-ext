"""PDS Catalog client for searching pre-scraped catalog data.

This client provides an in-memory search index for PDS datasets stored in JSONL format.
It supports filtering by node, mission, instrument, target, and temporal range.
"""

from loguru import logger
import os
from datetime import date
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

from akd_ext.tools.pds.utils.pds_catalog_api_models import PDSDataset, load_from_jsonl


# Default catalog directory containing scraped JSONL files
DEFAULT_CATALOG_DIR = Path(__file__).parent.parent / "pds_catalog" / "scraped_data"

# Response limits
MAX_RESULTS_LIMIT = 50
DEFAULT_RESULTS_LIMIT = 20

# Minimal mission abbreviations (only non-obvious ones)
# Many PDS3 datasets use abbreviated mission names in their IDs/titles
MISSION_ABBREVIATIONS: dict[str, list[str]] = {
    "juno": ["jno"],
    "cassini": ["co-"],
    "cassini huygens": ["co-"],
    "galileo": ["go-"],
    "voyager": ["vg1", "vg2"],
    "voyager 1": ["vg1"],
    "voyager 2": ["vg2"],
    "pioneer 10": ["p10"],
    "pioneer 11": ["p11"],
    "magellan": ["mgn"],
    "phoenix": ["phx"],
    "mars express": ["mex"],
}

# Minimal instrument abbreviations (only non-obvious ones)
INSTRUMENT_ABBREVIATIONS: dict[str, list[str]] = {
    "jade": ["jad"],
    "jedi": ["jed"],
    "magnetometer": ["mag", "fgm"],
    "fluxgate magnetometer": ["fgm"],
    "plasma wave": ["pws", "rpws", "wav"],
    "plasma spectrometer": ["caps", "pls"],
}

# Field profiles for response filtering
ESSENTIAL_FIELDS = {"id", "title", "node", "browse_url"}
SUMMARY_FIELDS = ESSENTIAL_FIELDS | {"missions", "targets", "instruments", "pds_version", "type"}
FULL_FIELDS = SUMMARY_FIELDS | {
    "description",
    "instrument_hosts",
    "data_types",
    "start_date",
    "stop_date",
    "keywords",
    "processing_level",
    "label_url",
    "source_url",
}
FIELD_PROFILES: dict[str, set[str]] = {
    "essential": ESSENTIAL_FIELDS,
    "summary": SUMMARY_FIELDS,
    "full": FULL_FIELDS,
}


class PDSCatalogClientError(Exception):
    """Base exception for PDS Catalog client errors."""

    pass


def _matches_term(
    dataset: PDSDataset,
    term: str,
    metadata_list: list[str],
    abbreviations: dict[str, list[str]],
) -> bool:
    """Check if term matches in metadata, title, or ID.

    Order of precedence:
    1. Metadata list (most accurate)
    2. Title substring (works for human-readable PDS4 titles)
    3. ID substring (works for abbreviated PDS3 IDs)
    4. Abbreviation lookup (fallback for non-obvious mappings)

    Args:
        dataset: The dataset to check
        term: The search term (e.g., mission or instrument name)
        metadata_list: The metadata field to check (e.g., dataset.missions or dataset.instruments)
        abbreviations: Mapping of terms to their abbreviations

    Returns:
        True if the term matches the dataset
    """
    term_lower = term.lower()

    # 1. Check metadata list
    if any(term_lower in m.lower() for m in metadata_list):
        return True

    # 2. Check title
    if term_lower in dataset.title.lower():
        return True

    # 3. Check ID
    if term_lower in dataset.id.lower():
        return True

    # 4. Check abbreviations
    for abbrev in abbreviations.get(term_lower, []):
        if abbrev in dataset.id.lower() or abbrev in dataset.title.lower():
            return True

    return False


def filter_dataset(dataset: PDSDataset, fields: set[str]) -> dict[str, Any]:
    """Filter dataset to specified fields."""
    result: dict[str, Any] = {}

    if "id" in fields:
        result["id"] = dataset.id
    if "title" in fields:
        result["title"] = dataset.title
    if "description" in fields and dataset.description:
        result["description"] = dataset.description
    if "node" in fields:
        result["node"] = dataset.node.value
    if "pds_version" in fields:
        result["pds_version"] = dataset.pds_version.value
    if "type" in fields:
        result["type"] = dataset.type.value
    if "missions" in fields and dataset.missions:
        result["missions"] = dataset.missions
    if "targets" in fields and dataset.targets:
        result["targets"] = dataset.targets
    if "instruments" in fields and dataset.instruments:
        result["instruments"] = dataset.instruments
    if "instrument_hosts" in fields and dataset.instrument_hosts:
        result["instrument_hosts"] = dataset.instrument_hosts
    if "data_types" in fields and dataset.data_types:
        result["data_types"] = dataset.data_types
    if "start_date" in fields and dataset.start_date:
        result["start_date"] = str(dataset.start_date)
    if "stop_date" in fields and dataset.stop_date:
        result["stop_date"] = str(dataset.stop_date)
    if "browse_url" in fields:
        result["browse_url"] = dataset.browse_url
    if "label_url" in fields and dataset.label_url:
        result["label_url"] = dataset.label_url
    if "source_url" in fields:
        result["source_url"] = dataset.source_url
    if "keywords" in fields and dataset.keywords:
        result["keywords"] = dataset.keywords
    if "processing_level" in fields and dataset.processing_level:
        result["processing_level"] = dataset.processing_level

    return result


class CatalogIndex:
    """In-memory index for the PDS catalog."""

    def __init__(self, datasets: list[PDSDataset]):
        """Initialize the catalog index.

        Args:
            datasets: List of PDSDataset objects
        """
        self.datasets = datasets
        self._by_node: dict[str, list[PDSDataset]] = {}
        self._by_mission: dict[str, list[PDSDataset]] = {}
        self._by_target: dict[str, list[PDSDataset]] = {}
        self._by_type: dict[str, list[PDSDataset]] = {}

        # Build indexes
        for ds in datasets:
            # By node
            node_key = ds.node.value
            if node_key not in self._by_node:
                self._by_node[node_key] = []
            self._by_node[node_key].append(ds)

            # By mission
            for mission in ds.missions:
                mission_lower = mission.lower()
                if mission_lower not in self._by_mission:
                    self._by_mission[mission_lower] = []
                self._by_mission[mission_lower].append(ds)

            # By target
            for target in ds.targets:
                target_lower = target.lower()
                if target_lower not in self._by_target:
                    self._by_target[target_lower] = []
                self._by_target[target_lower].append(ds)

            # By type (volume, bundle, collection)
            type_key = ds.type.value
            if type_key not in self._by_type:
                self._by_type[type_key] = []
            self._by_type[type_key].append(ds)

    def search(
        self,
        query: str | None = None,
        node: str | None = None,
        mission: str | None = None,
        instrument: str | None = None,
        target: str | None = None,
        pds_version: str | None = None,
        dataset_type: str | None = None,
        start_date: date | None = None,
        stop_date: date | None = None,
        limit: int = DEFAULT_RESULTS_LIMIT,
        offset: int = 0,
    ) -> tuple[list[PDSDataset], int]:
        """Search the catalog with filters.

        Args:
            query: Text search query
            node: Filter by PDS node
            mission: Filter by mission name
            instrument: Filter by instrument name
            target: Filter by target body
            pds_version: Filter by PDS version (PDS3 or PDS4)
            dataset_type: Filter by type (volume, bundle, collection)
            start_date: Filter datasets that have data on or after this date
            stop_date: Filter datasets that have data on or before this date
            limit: Maximum results to return
            offset: Skip first N results

        Returns:
            Tuple of (matching datasets, total count)
        """
        # Start with all datasets or filtered subset using indexes for speed
        if node:
            results = self._by_node.get(node.lower(), [])
        elif target:
            results = self._by_target.get(target.lower(), [])
        else:
            results = self.datasets

        # Apply mission filter with fallback to ID/title matching
        if mission:
            results = [d for d in results if _matches_term(d, mission, d.missions, MISSION_ABBREVIATIONS)]

        # Apply instrument filter with fallback to ID/title matching
        if instrument:
            results = [d for d in results if _matches_term(d, instrument, d.instruments, INSTRUMENT_ABBREVIATIONS)]

        # Apply target filter — always apply when target is specified,
        # even if node was also used to narrow the initial set
        if target:
            target_lower = target.lower()
            results = [d for d in results if any(target_lower in t.lower() for t in d.targets)]

        if pds_version:
            results = [d for d in results if d.pds_version.value == pds_version.upper()]

        # Filter by dataset type
        if dataset_type:
            results = [d for d in results if d.type.value == dataset_type.lower()]

        # Temporal filtering - find datasets that overlap with the requested date range
        if start_date:
            # Include datasets that end on or after the requested start date
            results = [d for d in results if d.stop_date is None or d.stop_date >= start_date]
        if stop_date:
            # Include datasets that start on or before the requested stop date
            results = [d for d in results if d.start_date is None or d.start_date <= stop_date]

        # Apply text search with fuzzy matching
        if query:
            query_lower = query.lower()
            scored_results = []
            # Use lower threshold for short queries (acronyms like "JADE", "JEDI")
            threshold = 60 if len(query_lower) <= 5 else 70
            for d in results:
                search_text = d.to_search_text()
                # Use partial ratio for substring-like matching
                # and token_set_ratio for word reordering tolerance
                score = max(
                    fuzz.partial_ratio(query_lower, search_text),
                    fuzz.token_set_ratio(query_lower, search_text),
                )

                # Boost score for exact substring matches on short queries
                # This helps "JADE" match datasets with "JAD" in the title
                # (PDS datasets often use abbreviated forms like "JAD" for "JADE")
                if len(query_lower) <= 5:
                    if query_lower in search_text:
                        # Exact substring match gets high score
                        score = max(score, 95)
                    elif len(query_lower) > 2 and query_lower[:-1] in search_text:
                        # "JADE" matches "JAD" (remove last char)
                        score = max(score, 90)
                    elif len(query_lower) > 3 and query_lower[:-2] in search_text:
                        # "JEDI" matches "JED" (remove last 2 chars)
                        score = max(score, 85)

                if score >= threshold:
                    scored_results.append((score, d))
            # Sort by score descending
            scored_results.sort(key=lambda x: x[0], reverse=True)
            results = [d for _, d in scored_results]

        total = len(results)
        paginated = results[offset : offset + limit]

        return paginated, total

    @staticmethod
    def _normalize_id(raw_id: str) -> str:
        """Normalize a dataset ID by stripping set/tuple notation artifacts."""
        import re

        cleaned = raw_id.strip()
        cleaned = re.sub(r'^[\(\{\["\s]+', "", cleaned)
        cleaned = re.sub(r'[,\)\}\]"\s]+$', "", cleaned)
        return cleaned

    def get_dataset_by_id(self, dataset_id: str) -> PDSDataset | None:
        """Get a dataset by its ID.

        Performs exact match first, then falls back to normalized comparison
        to handle malformed IDs from catalog scraping.

        Args:
            dataset_id: The dataset ID (LIDVID for PDS4, VOLUME_ID for PDS3)

        Returns:
            The dataset if found, None otherwise
        """
        for dataset in self.datasets:
            if dataset.id == dataset_id:
                return dataset

        normalized_query = self._normalize_id(dataset_id)
        for dataset in self.datasets:
            if self._normalize_id(dataset.id) == normalized_query:
                return dataset

        return None

    def find_similar_dataset_ids(self, dataset_id: str, max_suggestions: int = 5) -> list[tuple[str, int]]:
        """Find dataset IDs similar to the given ID using fuzzy matching.

        Args:
            dataset_id: The dataset ID to find similar matches for
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of (dataset_id, similarity_score) tuples, sorted by score descending
        """
        scored = []
        dataset_id_lower = dataset_id.lower()
        for dataset in self.datasets:
            score = max(
                fuzz.ratio(dataset_id_lower, dataset.id.lower()),
                fuzz.partial_ratio(dataset_id_lower, dataset.id.lower()),
            )
            if score >= 50:
                scored.append((dataset.id, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:max_suggestions]

    def get_stats(self) -> dict[str, Any]:
        """Get catalog statistics."""
        stats = {
            "total_datasets": len(self.datasets),
            "by_node": {k: len(v) for k, v in sorted(self._by_node.items())},
            "by_pds_version": {},
            "by_type": {k: len(v) for k, v in sorted(self._by_type.items())},
            "missions_count": len(self._by_mission),
            "targets_count": len(self._by_target),
        }

        # Count by PDS version
        for ds in self.datasets:
            version = ds.pds_version.value
            stats["by_pds_version"][version] = stats["by_pds_version"].get(version, 0) + 1

        return stats

    def list_missions(self, node: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """List all missions with dataset counts.

        Args:
            node: Filter by PDS node (optional)
            limit: Maximum missions to return

        Returns:
            List of missions with counts and nodes
        """
        missions = []
        for mission, datasets in sorted(self._by_mission.items()):
            mission_data = {
                "name": datasets[0].missions[0] if datasets else mission,  # Use proper casing
                "count": len(datasets),
                "nodes": list({d.node.value for d in datasets}),
            }

            if node and node.lower() not in mission_data["nodes"]:
                continue

            missions.append(mission_data)

        return missions[:limit]

    def list_targets(self, node: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """List all targets with dataset counts.

        Args:
            node: Filter by PDS node (optional)
            limit: Maximum targets to return

        Returns:
            List of targets with counts and nodes
        """
        targets = []
        for target, datasets in sorted(self._by_target.items()):
            target_data = {
                "name": datasets[0].targets[0] if datasets else target,  # Use proper casing
                "count": len(datasets),
                "nodes": list({d.node.value for d in datasets}),
            }

            if node and node.lower() not in target_data["nodes"]:
                continue

            targets.append(target_data)

        return targets[:limit]


class PDSCatalogClient:
    """Client for accessing the PDS Catalog.

    This client loads JSONL catalog files and provides search capabilities.
    """

    def __init__(self, catalog_dir: str | Path | None = None):
        """Initialize the catalog client.

        Args:
            catalog_dir: Directory containing catalog JSONL files. If None, uses default location
                        or PDS_CATALOG_DIR environment variable.
        """
        if catalog_dir is None:
            catalog_dir = Path(os.getenv("PDS_CATALOG_DIR", str(DEFAULT_CATALOG_DIR)))
        else:
            catalog_dir = Path(catalog_dir)

        self._catalog_dir = catalog_dir
        self._index: CatalogIndex | None = None

    def _load_catalog(self) -> CatalogIndex:
        """Load catalog from JSONL files."""
        all_datasets: list[PDSDataset] = []

        if self._catalog_dir.is_dir():
            for jsonl_file in self._catalog_dir.glob("*_catalog.jsonl"):
                # Skip test files
                if "test" in jsonl_file.name:
                    continue
                logger.info(f"Loading catalog from {jsonl_file}")
                datasets = load_from_jsonl(jsonl_file)
                all_datasets.extend(datasets)
        elif self._catalog_dir.is_file():
            # Backwards compat: single file
            logger.info(f"Loading catalog from {self._catalog_dir}")
            all_datasets = load_from_jsonl(self._catalog_dir)

        if not all_datasets:
            logger.warning(f"No catalog files found in: {self._catalog_dir}")
            logger.warning("The catalog may be empty or the directory may not exist.")

        return CatalogIndex(all_datasets)

    @property
    def index(self) -> CatalogIndex:
        """Get the catalog index, loading it if necessary."""
        if self._index is None:
            self._index = self._load_catalog()
        return self._index

    async def search(
        self,
        query: str | None = None,
        node: str | None = None,
        mission: str | None = None,
        instrument: str | None = None,
        target: str | None = None,
        pds_version: str | None = None,
        dataset_type: str | None = None,
        start_date: date | None = None,
        stop_date: date | None = None,
        limit: int = DEFAULT_RESULTS_LIMIT,
        offset: int = 0,
    ) -> tuple[list[PDSDataset], int]:
        """Search the catalog.

        Args:
            query: Text search query
            node: Filter by PDS node
            mission: Filter by mission name
            instrument: Filter by instrument name
            target: Filter by target body
            pds_version: Filter by PDS version (PDS3 or PDS4)
            dataset_type: Filter by type (volume, bundle, collection)
            start_date: Filter datasets that have data on or after this date
            stop_date: Filter datasets that have data on or before this date
            limit: Maximum results to return
            offset: Skip first N results

        Returns:
            Tuple of (matching datasets, total count)
        """
        return self.index.search(
            query=query,
            node=node,
            mission=mission,
            instrument=instrument,
            target=target,
            pds_version=pds_version,
            dataset_type=dataset_type,
            start_date=start_date,
            stop_date=stop_date,
            limit=limit,
            offset=offset,
        )

    async def get_dataset(self, dataset_id: str) -> PDSDataset | None:
        """Get a dataset by ID.

        Args:
            dataset_id: The dataset ID

        Returns:
            The dataset if found, None otherwise
        """
        return self.index.get_dataset_by_id(dataset_id)

    async def list_missions(self, node: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """List all missions.

        Args:
            node: Filter by PDS node (optional)
            limit: Maximum missions to return

        Returns:
            List of missions with counts
        """
        return self.index.list_missions(node=node, limit=limit)

    async def list_targets(self, node: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """List all targets.

        Args:
            node: Filter by PDS node (optional)
            limit: Maximum targets to return

        Returns:
            List of targets with counts
        """
        return self.index.list_targets(node=node, limit=limit)

    async def get_stats(self) -> dict[str, Any]:
        """Get catalog statistics.

        Returns:
            Statistics about the catalog
        """
        return self.index.get_stats()
