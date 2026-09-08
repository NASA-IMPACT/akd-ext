"""Operation handlers behind ``psi_api_tool``.

Each ``async def op_*`` performs one PSI/DataCite operation and returns a
result slice ``{data, summary, warnings, sources, raw}``. ``raw`` is the raw
upstream JSON (or None) that the tool attaches only when the caller asks for
``response_mode`` raw/both. Keeping the logic here (rather than on the tool)
lets the dispatcher stay thin and keeps each operation independently testable.
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence
from urllib.parse import quote

import httpx

from ._client import (
    DownloadUrlExpiredError,
    ensure_allowed_download_url,
    get_json,
    make_async_client,
)
from ._normalize import (
    absolute_psi_url,
    matches_file_filters,
    normalize_datacite,
    normalize_discovery_record,
    normalize_file_record,
    normalize_investigation,
    normalize_investigation_id,
    normalize_selector,
    relevance_score,
    safe_segment,
)

if TYPE_CHECKING:  # avoid a runtime import cycle with api.py
    from .api import PsiApiConfig, PsiApiInput


def store_json_artifact(artifact_root: str, value: Any, prefix: str) -> dict:
    """Write a JSON artifact and return its id, path, and size."""
    import json

    artifact_id = f"{prefix}_{uuid.uuid4().hex[:12]}"
    path = Path(artifact_root) / f"{artifact_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    path.write_text(body, encoding="utf-8")
    return {"artifact_id": artifact_id, "path": str(path), "size_bytes": len(body.encode("utf-8"))}


async def fetch_file_groups(
    config: PsiApiConfig,
    selector: str,
    file_type: str = "all",
    *,
    pattern: str | None = None,
    category: str | None = None,
    subcategory: str | None = None,
    subdirectory_prefix: str | None = None,
    allowed_categories: Sequence[str] | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> tuple[list[dict], dict, list[dict]]:
    """Query PSI file search; return (per-study groups, source metadata, warnings)."""
    url = config.file_search_url_template.format(investigation_selector=normalize_selector(selector))
    params = {"type": file_type} if file_type != "all" else None
    async with make_async_client(config, transport) as client:
        raw = await get_json(client, url, params=params)
    if not isinstance(raw, dict) or not isinstance(raw.get("studies"), dict):
        raise RuntimeError("The PSI file-search response does not contain a studies object.")

    groups: list[dict] = []
    warnings: list[dict] = []
    for study_key, study_value in raw["studies"].items():
        if not isinstance(study_value, dict):
            continue
        investigation_id = normalize_investigation_id(study_key)
        study_files = study_value.get("study_files")
        records = [
            normalize_file_record(investigation_id, item)
            for item in (study_files if isinstance(study_files, list) else [])
            if isinstance(item, dict)
        ]
        reported = int(study_value.get("file_count") or len(records))
        if reported != len(records):
            warnings.append(
                {
                    "code": "FILE_COUNT_MISMATCH",
                    "message": f"PSI reported {reported} files for {investigation_id} but returned {len(records)}.",
                }
            )
        matched = [
            record
            for record in records
            if matches_file_filters(
                record,
                pattern=pattern,
                category=category,
                subcategory=subcategory,
                subdirectory_prefix=subdirectory_prefix,
                allowed_categories=allowed_categories,
            )
        ]
        groups.append(
            {
                "investigation_id": investigation_id,
                "reported_file_count": reported,
                "returned_file_count": len(records),
                "matched_file_count": len(matched),
                "files": matched,
            }
        )
    source_metadata = {
        "investigation_hits": raw.get("hits"),
        "total_hits": raw.get("total_hits"),
        "page_number": raw.get("page_number"),
        "page_size": raw.get("page_size"),
        "page_total": raw.get("page_total"),
        "valid_input": raw.get("valid_input"),
    }
    return groups, source_metadata, warnings


def _build_dataset_tree(files: list[dict]) -> list[dict]:
    """Group normalized file records into category > subcategory > directory nodes."""
    categories: dict[str, dict[str, dict[str, dict]]] = {}
    for record in files:
        category = record["category"] or "Uncategorized"
        subcategory = record["subcategory"] or "Unspecified"
        directory = record["subdirectory"] or "Root"
        leaf = (
            categories.setdefault(category, {})
            .setdefault(subcategory, {})
            .setdefault(directory, {"files": [], "types": {}})
        )
        leaf["files"].append(record["file_name"])
        extension = record["extension"] or "(none)"
        leaf["types"][extension] = leaf["types"].get(extension, 0) + 1

    tree = []
    for category in sorted(categories):
        subcategory_nodes = []
        for subcategory in sorted(categories[category]):
            directory_nodes = []
            for directory in sorted(categories[category][subcategory]):
                leaf = categories[category][subcategory][directory]
                directory_nodes.append(
                    {
                        "name": directory,
                        "type": "directory",
                        "file_count": len(leaf["files"]),
                        "file_types": leaf["types"],
                        "representative_files": leaf["files"][:5],
                    }
                )
            subcategory_nodes.append(
                {
                    "name": subcategory,
                    "type": "subcategory",
                    "file_count": sum(node["file_count"] for node in directory_nodes),
                    "children": directory_nodes,
                }
            )
        tree.append(
            {
                "name": category,
                "type": "category",
                "file_count": sum(node["file_count"] for node in subcategory_nodes),
                "children": subcategory_nodes,
            }
        )
    return tree


# ---- operations ----


async def op_discover(config: PsiApiConfig, params: PsiApiInput, transport=None) -> dict:
    """List public investigations, optionally ranked by keyword relevance."""
    async with make_async_client(config, transport) as client:
        raw = await get_json(client, config.discovery_url)
    if not isinstance(raw, list):
        raise RuntimeError(f"PSI discovery response was {type(raw).__name__}, expected a list.")

    investigations = [normalize_discovery_record(item) for item in raw]
    if params.query:
        for item in investigations:
            score, reasons = relevance_score(
                params.query,
                [
                    ("Title", 0.45, item.get("title")),
                    ("Objective", 0.40, item.get("objective")),
                    ("Accession", 0.15, item.get("investigation_id")),
                ],
            )
            item["match_score"] = score
            item["match_reasons"] = reasons
        investigations.sort(key=lambda item: item.get("match_score", 0), reverse=True)

    total = len(investigations)
    returned = investigations[: params.max_items]
    summary = f"Found {total} public PSI investigations"
    summary += (
        f" and returned the {len(returned)} best matches for {params.query!r}."
        if params.query
        else f"; returned {len(returned)}."
    )
    return {
        "data": {"investigations": returned, "total_available": total},
        "summary": summary,
        "warnings": [],
        "sources": [{"type": "psi_api", "resource": "public-investigation-metadata"}],
        "raw": raw,
    }


async def op_get_investigation(config: PsiApiConfig, params: PsiApiInput, transport=None) -> dict:
    """Retrieve normalized metadata for one investigation."""
    investigation_id = normalize_investigation_id(params.investigation_id)
    url = config.investigation_url_template.format(investigation_id=investigation_id)
    query = {"fields": ",".join(params.fields)} if params.fields else None
    async with make_async_client(config, transport) as client:
        raw = await get_json(client, url, params=query)
    if not isinstance(raw, dict):
        raise RuntimeError(f"PSI investigation response was {type(raw).__name__}, expected an object.")

    investigation = normalize_investigation(raw)
    title = investigation.get("title") or "untitled investigation"
    return {
        "data": {"investigation": investigation},
        "summary": f"Retrieved metadata for {investigation_id}: {title}.",
        "warnings": [],
        "sources": [{"type": "psi_api", "resource": investigation_id}],
        "raw": raw,
    }


async def op_search_files(config: PsiApiConfig, params: PsiApiInput, transport=None) -> dict:
    """Search investigation files with filters; truncate and spill overflow to an artifact.

    Results are restricted to the categories in ``config.search_categories``
    (default: Reports). An empty list disables the restriction.
    """
    selector = params.investigation_selector or params.investigation_id
    scope = [item for item in (config.search_categories or []) if str(item).strip()]
    groups, source_metadata, warnings = await fetch_file_groups(
        config,
        selector,
        params.file_type,
        pattern=params.file_name_pattern,
        category=params.category,
        subcategory=params.subcategory,
        subdirectory_prefix=params.subdirectory_prefix,
        allowed_categories=scope or None,
        transport=transport,
    )
    if scope and params.category and params.category.casefold() not in {item.casefold() for item in scope}:
        warnings.append(
            {
                "code": "CATEGORY_OUT_OF_SCOPE",
                "message": f"Requested category {params.category!r} is outside the current search scope "
                f"({', '.join(scope)}). Set search_categories (env PSI_SEARCH_CATEGORIES) to broaden it.",
            }
        )
    received = sum(group["returned_file_count"] for group in groups)
    matched = sum(group["matched_file_count"] for group in groups)
    truncated = matched > params.max_items

    returned_groups: list[dict] = []
    remaining = params.max_items
    for group in groups:
        if remaining <= 0:
            break
        files = group["files"][:remaining]
        remaining -= len(files)
        returned_groups.append({**group, "files": files})

    returned = min(matched, params.max_items)
    result_limits = {
        "files_received_from_api": received,
        "files_matching_filters": matched,
        "files_returned_to_agent": returned,
        "truncated": truncated,
        "category_scope": scope,
    }
    if truncated:
        result_limits["complete_inventory_artifact"] = store_json_artifact(
            config.artifact_root, {"investigations": groups}, prefix="file_inventory"
        )
    summary = (
        f"The PSI API returned {received} file records; {matched} matched the requested "
        f"filters and {returned} were included inline."
    )
    if scope:
        summary += f" Search was scoped to categories: {', '.join(scope)}."
    return {
        "data": {
            "investigations": returned_groups,
            "result_limits": result_limits,
            "source_metadata": source_metadata,
        },
        "summary": summary,
        "warnings": warnings,
        "sources": [{"type": "psi_api", "resource": f"files:{selector}"}],
        "raw": None,
    }


async def op_navigate_dataset(config: PsiApiConfig, params: PsiApiInput, transport=None) -> dict:
    """Summarize an investigation's files as a category/subcategory/directory tree."""
    investigation_id = normalize_investigation_id(params.investigation_id)
    selector = investigation_id.split("-")[1]
    groups, _, warnings = await fetch_file_groups(
        config,
        selector,
        params.file_type,
        pattern=params.file_name_pattern,
        category=params.category,
        subcategory=params.subcategory,
        subdirectory_prefix=params.subdirectory_prefix,
        transport=transport,
    )
    files = [record for group in groups for record in group["files"]]
    scanned = sum(group["returned_file_count"] for group in groups)
    return {
        "data": {
            "investigation_id": investigation_id,
            "tree": _build_dataset_tree(files),
            "totals": {"files_scanned": scanned, "files_matching_filters": len(files)},
        },
        "summary": f"Built a dataset tree from {scanned} PSI file records.",
        "warnings": warnings,
        "sources": [{"type": "psi_api", "resource": f"files:{selector}"}],
        "raw": None,
    }


async def _find_file_record(config: PsiApiConfig, investigation_id: str, file_name: str, transport=None) -> dict:
    """Resolve an exact file name to its normalized PSI file record."""
    selector = normalize_investigation_id(investigation_id).split("-")[1]
    groups, _, _ = await fetch_file_groups(config, selector, pattern=file_name, transport=transport)
    matches = [record for group in groups for record in group["files"] if record["file_name"] == file_name]
    if not matches:
        raise RuntimeError(f"File {file_name!r} was not found in {investigation_id}.")
    if len(matches) > 1:
        paths = ", ".join(record["logical_path"] for record in matches)
        raise RuntimeError(f"More than one file matched {file_name!r}: {paths}. Pass remote_url instead.")
    return matches[0]


async def _download_to_artifact(
    config: PsiApiConfig, params: PsiApiInput, url: str, record: dict | None, transport=None
) -> dict:
    """Stream one PSI download to disk with size guards and a SHA-256 integrity check."""
    ensure_allowed_download_url(url)
    file_name = params.file_name or (record or {}).get("file_name") or "downloaded_file"
    base = Path(params.destination) if params.destination else Path(config.download_root)
    if params.preserve_folder_structure and record:
        relative = Path(*record["logical_path"].split("/"))
    else:
        relative = Path(safe_segment(file_name))
    destination = base / relative
    destination.parent.mkdir(parents=True, exist_ok=True)

    digest = hashlib.sha256()
    total = 0
    async with make_async_client(config, transport) as client:
        try:
            async with client.stream("GET", url) as response:
                if response.status_code in (401, 403):
                    raise DownloadUrlExpiredError(f"PSI download URL rejected ({response.status_code}).")
                if response.status_code >= 400:
                    raise RuntimeError(f"PSI download failed ({response.status_code}) for {url}.")
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > config.max_download_bytes:
                    raise RuntimeError(
                        f"File is {content_length} bytes, above the {config.max_download_bytes}-byte download limit."
                    )
                with destination.open("wb") as handle:
                    async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                        total += len(chunk)
                        if total > config.max_download_bytes:
                            raise RuntimeError("The download exceeded the configured size limit while streaming.")
                        digest.update(chunk)
                        handle.write(chunk)
                mime_type = response.headers.get("content-type")
        except httpx.TimeoutException as exc:
            destination.unlink(missing_ok=True)
            raise TimeoutError(f"PSI download timed out: {url}") from exc
        except Exception:
            destination.unlink(missing_ok=True)
            raise

    investigation_id = normalize_investigation_id(params.investigation_id)
    return {
        "data": {
            "artifact_id": f"psi_file_{uuid.uuid4().hex[:12]}",
            "investigation_id": investigation_id,
            "file_name": file_name,
            "path": str(destination),
            "logical_path": record["logical_path"] if record else str(relative),
            "mime_type": mime_type,
            "size_bytes": total,
            "sha256": digest.hexdigest(),
        },
        "summary": f"Downloaded {file_name} ({total} bytes) to {destination}.",
        "warnings": list((record or {}).get("risk_flags") or []),
        "sources": [{"type": "psi_api", "resource": investigation_id, "file_name": file_name}],
        "raw": None,
    }


async def op_retrieve_file(config: PsiApiConfig, params: PsiApiInput, transport=None) -> dict:
    """Download one public file, refreshing an expired signed URL once when possible."""
    record = None
    if params.file_name:
        record = await _find_file_record(config, params.investigation_id, params.file_name, transport)
    remote_url = params.remote_url or (record or {}).get("remote_url")
    if not remote_url:
        raise RuntimeError("No PSI download URL was available for the requested file.")

    url = absolute_psi_url(config.psi_origin, str(remote_url))
    try:
        return await _download_to_artifact(config, params, url, record, transport)
    except DownloadUrlExpiredError:
        if not params.file_name:
            raise
        record = await _find_file_record(config, params.investigation_id, params.file_name, transport)
        url = absolute_psi_url(config.psi_origin, str(record.get("remote_url")))
        result = await _download_to_artifact(config, params, url, record, transport)
        result["warnings"].append(
            {
                "code": "DOWNLOAD_URL_REFRESHED",
                "message": "The PSI download URL was refreshed and retried once.",
            }
        )
        return result


async def op_lookup_publication(config: PsiApiConfig, params: PsiApiInput, transport=None) -> dict:
    """Resolve a DOI against the DataCite registry."""
    url = config.datacite_doi_url_template.format(doi=quote(params.doi, safe="/"))
    async with make_async_client(config, transport) as client:
        raw = await get_json(client, url)
    if not isinstance(raw, dict):
        raise RuntimeError(f"DataCite response was {type(raw).__name__}, expected an object.")

    publication = normalize_datacite(raw)
    return {
        "data": {"publication": publication},
        "summary": f"Retrieved DataCite metadata for DOI {publication.get('doi') or params.doi}.",
        "warnings": [],
        "sources": [{"type": "datacite", "doi": params.doi}],
        "raw": raw,
    }


OPERATIONS = {
    "discover_investigations": op_discover,
    "get_investigation": op_get_investigation,
    "search_files": op_search_files,
    "navigate_dataset": op_navigate_dataset,
    "retrieve_file": op_retrieve_file,
    "lookup_publication": op_lookup_publication,
}
