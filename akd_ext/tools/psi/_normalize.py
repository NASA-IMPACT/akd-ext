"""Normalization and scoring helpers shared by the PSI tools.

Ported from the standalone ``psi-agent-tools`` reference implementation so that
ID normalization, keyword relevance scoring, and record shaping behave
identically against the live PSI API.
"""

import re
from fnmatch import fnmatch
from pathlib import PurePosixPath
from urllib.parse import urljoin

_INVESTIGATION_RE = re.compile(r"^(?:PSI-)?(\d+)$", re.IGNORECASE)
_SELECTOR_RE = re.compile(r"^\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*$")
_TOKEN_RE = re.compile(r"[a-z0-9]+")

LEGACY_RISK_FLAG = {
    "code": "LEGACY_MISSING_RISK",
    "message": "This file is stored under a legacy path and may no longer be available.",
}


def normalize_investigation_id(value: str) -> str:
    """Accept ``117`` / ``PSI-117`` / ``psi-117`` and return canonical ``PSI-117``."""
    match = _INVESTIGATION_RE.fullmatch(str(value).strip())
    if not match:
        raise ValueError(f"Invalid PSI investigation id {value!r}; expected forms like '117' or 'PSI-117'.")
    return f"PSI-{int(match.group(1))}"


def normalize_selector(value: str) -> str:
    """Validate a PSI multi-investigation selector such as ``117``, ``4,10``, or ``20-25``."""
    cleaned = re.sub(r"psi-", "", str(value).strip().replace(" ", ""), flags=re.IGNORECASE)
    if not _SELECTOR_RE.fullmatch(cleaned):
        raise ValueError(f"Invalid investigation selector {value!r}; use values such as 117, 4,10, or 20-25.")
    for item in cleaned.split(","):
        if "-" in item:
            start, end = item.split("-")
            if int(start) > int(end):
                raise ValueError(f"Invalid descending range: {item}")
    return cleaned


def safe_segment(value: str) -> str:
    """Sanitize one path component for local filesystem use."""
    segment = str(value).replace("\\", "_").replace("/", "_").strip()
    segment = re.sub(r"[\x00-\x1f<>:\"|?*]", "_", segment)
    segment = re.sub(r"\s+", " ", segment).strip(" .")
    if segment in {"", ".", ".."}:
        return "_"
    return segment[:240]


def logical_path(file_record: dict) -> str:
    """Build the canonical ``PSI-n/category/subcategory/subdir/file`` path for a file record."""
    parts: list[str] = [file_record.get("investigation_id", "PSI-UNKNOWN")]
    for key in ("category", "subcategory", "subdirectory"):
        raw = str(file_record.get(key) or "").strip()
        if not raw:
            continue
        for component in re.split(r"[\\/]", raw):
            if component.strip():
                parts.append(safe_segment(component))
    parts.append(safe_segment(str(file_record.get("file_name") or "unnamed")))
    return "/".join(parts)


def absolute_psi_url(origin: str, remote_url: str) -> str:
    """Resolve a possibly relative PSI download URL against the PSI origin."""
    return urljoin(origin.rstrip("/") + "/", remote_url)


def matches_file_filters(
    record: dict,
    *,
    pattern: str | None = None,
    category: str | None = None,
    subcategory: str | None = None,
    subdirectory_prefix: str | None = None,
) -> bool:
    """Apply the optional file filters (AND semantics, case-insensitive)."""
    if pattern and not fnmatch(str(record.get("file_name", "")).lower(), pattern.lower()):
        return False
    if category and str(record.get("category", "")).casefold() != category.casefold():
        return False
    if subcategory and str(record.get("subcategory", "")).casefold() != subcategory.casefold():
        return False
    if subdirectory_prefix and not str(record.get("subdirectory", "")).casefold().startswith(
        subdirectory_prefix.casefold()
    ):
        return False
    return True


def tokenize(value: str | None) -> set[str]:
    """Lowercase alphanumeric token set used for relevance scoring."""
    return set(_TOKEN_RE.findall((value or "").lower()))


def relevance_score(query: str | None, fields: list[tuple[str, float, str | None]]) -> tuple[float, list[str]]:
    """Score keyword overlap between a query and weighted text fields.

    Returns a 0..1 weighted-coverage score (rounded to 4 decimals) plus
    human-readable match reasons. Empty fields still count toward the total
    weight so missing metadata dilutes the score, matching the reference tool.
    """
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0, []

    total_weight = 0.0
    weighted_score = 0.0
    reasons: list[str] = []
    for label, weight, text in fields:
        total_weight += weight
        field_tokens = tokenize(text)
        if not field_tokens:
            continue
        overlap = query_tokens & field_tokens
        coverage = len(overlap) / len(query_tokens)
        weighted_score += coverage * weight
        if overlap:
            display = ", ".join(sorted(overlap)[:6])
            reasons.append(f"{label} matches: {display}")
    score = weighted_score / total_weight if total_weight else 0.0
    return round(min(score, 1.0), 4), reasons


def normalize_discovery_record(record: dict) -> dict:
    """Flatten one raw discovery record into the summary shape used by the tools."""
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    accession = record.get("accession") or record.get("accession_id")
    investigation_id = normalize_investigation_id(str(accession))
    return {
        "investigation_id": investigation_id,
        "accession_id": record.get("accession_id") or int(investigation_id.split("-")[1]),
        "title": metadata.get("investigation_title") or record.get("title") or "",
        "objective": metadata.get("investigation_objective") or record.get("objective") or "",
        "public_release_date": metadata.get("public_release_date") or record.get("releaseDate"),
        "public": bool(record.get("public", True)),
        "date_created": record.get("date_created"),
        "date_modified": record.get("date_modified"),
    }


def normalize_publication(item: dict) -> dict:
    """Normalize one publication entry from a PSI investigation record."""
    status = item.get("status")
    if isinstance(status, dict):
        status = status.get("annotationValue") or status.get("termAccession")
    return {
        "title": item.get("title"),
        "doi": item.get("doi") or None,
        "authors": item.get("authorList") or item.get("authors"),
        "status": status,
    }


def normalize_investigation(record: dict) -> dict:
    """Normalize a full PSI investigation record (camelCase upstream keys included)."""
    investigation_id = normalize_investigation_id(str(record.get("accession") or record.get("investigation_id")))
    publications = [normalize_publication(item) for item in record.get("publications") or [] if isinstance(item, dict)]
    return {
        "investigation_id": investigation_id,
        "title": record.get("title") or record.get("proposalTitle") or "",
        "objective": record.get("objective") or record.get("description") or "",
        "approach": record.get("approach") or "",
        "hypothesis": record.get("hypothesis") or "",
        "research_area": record.get("researchArea") or record.get("research_area"),
        "sub_research_area": record.get("subResearchArea") or record.get("sub_research_area"),
        "gravity_setting": record.get("gravitySetting"),
        "project_type": record.get("projectType"),
        "mission": record.get("missionName") or record.get("mission"),
        "space_program": record.get("spaceProgram"),
        "experiment_hardware": record.get("experimentHardware"),
        "start_date": record.get("investigationStartDate"),
        "end_date": record.get("investigationEndDate"),
        "release_date": record.get("releaseDate"),
        "modified_date": record.get("modifiedDate"),
        "doi": record.get("doi") or None,
        "public": bool(record.get("public", True)),
        "license": {
            "name": record.get("licenseName"),
            "identifier": record.get("licenseIdentifier"),
            "link": record.get("licenseLink"),
        },
        "keywords": record.get("keywords") or [],
        "related_investigations": record.get("related_glds") or record.get("relatedInvestigations"),
        "research_impacts": record.get("researchImpacts"),
        "publications": publications,
        "publication_count": len(publications),
        "total_file_size": record.get("totalFileSize"),
    }


def normalize_file_record(investigation_id: str, record: dict) -> dict:
    """Normalize one PSI file-search record and attach its logical path and risk flags."""
    file_name = str(record.get("file_name") or "")
    result = {
        "investigation_id": normalize_investigation_id(investigation_id),
        "file_name": file_name,
        "file_size_bytes": int(record.get("file_size") or 0),
        "category": record.get("category") or "",
        "subcategory": record.get("subcategory") or "",
        "subdirectory": record.get("subdirectory") or "",
        "extension": PurePosixPath(file_name).suffix.lower(),
        "organization": record.get("organization"),
        "restricted": bool(record.get("restricted", False)),
        "visible": bool(record.get("visible", True)),
        "remote_url": record.get("remote_url"),
        "date_created": record.get("date_created"),
        "date_updated": record.get("date_updated"),
        "risk_flags": [],
    }
    haystack = f"{result['remote_url'] or ''} {result['subdirectory']}".lower()
    if "/legacy/" in haystack:
        result["risk_flags"].append(dict(LEGACY_RISK_FLAG))
    result["logical_path"] = logical_path(result)
    return result


def normalize_datacite(payload: dict) -> dict:
    """Normalize a DataCite DOI response into a flat publication record."""
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    attributes = data.get("attributes") if isinstance(data.get("attributes"), dict) else {}
    titles = [t.get("title") for t in attributes.get("titles") or [] if isinstance(t, dict) and t.get("title")]
    publisher = attributes.get("publisher")
    if isinstance(publisher, dict):
        publisher = publisher.get("name")
    types = attributes.get("types") if isinstance(attributes.get("types"), dict) else {}
    return {
        "doi": attributes.get("doi") or data.get("id"),
        "title": titles[0] if titles else None,
        "creators": [c.get("name") for c in attributes.get("creators") or [] if isinstance(c, dict)],
        "publisher": publisher,
        "publication_year": attributes.get("publicationYear"),
        "resource_type": types.get("resourceTypeGeneral") or types.get("resourceType"),
        "url": attributes.get("url"),
        "subjects": [s.get("subject") for s in attributes.get("subjects") or [] if isinstance(s, dict)],
        "rights": attributes.get("rightsList") or [],
        "related_identifiers": attributes.get("relatedIdentifiers") or [],
        "state": attributes.get("state"),
    }
