"""Utility functions for EIE tools."""

from datetime import datetime, timezone


def bboxes_overlap(bbox1: list[float], bbox2: list[float]) -> bool:
    """Check if two bounding boxes overlap.
    
    Args:
        bbox1: First bounding box as [west, south, east, north]
        bbox2: Second bounding box in the same format
    
    Returns:
        True if the boxes overlap, False otherwise
    """
    if len(bbox1) < 4 or len(bbox2) < 4:
        return False
    
    w1, s1, e1, n1 = bbox1[:4]
    w2, s2, e2, n2 = bbox2[:4]
    
    # Two boxes do NOT overlap if one is entirely to the left, right, above, or below
    return not (e1 < w2 or e2 < w1 or n1 < s2 or n2 < s1)


def parse_iso_date(s: str | None) -> datetime | None:
    """Parse ISO-8601 date string to UTC-aware datetime."""
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError):
        return None


def intervals_overlap(interval: list[str | None], start: str, end: str) -> bool:
    """Check if a collection's temporal interval overlaps with a requested time range.
    
    Args:
        interval: Collection's temporal interval as [start, end] ISO-8601 strings
        start: Requested range start as ISO-8601 string
        end: Requested range end as ISO-8601 string
    
    Returns:
        True if the intervals overlap, False otherwise
    """
    if not interval or len(interval) < 2:
        return False
    
    col_start = parse_iso_date(interval[0])
    col_end = parse_iso_date(interval[1])
    req_start = parse_iso_date(start)
    req_end = parse_iso_date(end)
    
    # Open-ended intervals: assume overlap if we can't determine otherwise
    if (req_start is None and req_end is None) or (col_start is None and col_end is None):
        return True
    
    # Collection ends before requested range starts → no overlap
    if col_end and req_start and col_end < req_start:
        return False
    
    # Collection starts after requested range ends → no overlap
    if col_start and req_end and col_start > req_end:
        return False
    
    return True
