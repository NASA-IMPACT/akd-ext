import re


def validate_datetime(datetime_str: str | None) -> tuple[str | None, str | None]:
    """Validate and normalize ISO-8601 datetime range.

    Args:
        datetime_str: Expected format "YYYY-MM-DD/YYYY-MM-DD" or with time "YYYY-MM-DDTHH:MM:SSZ/..."

    Returns:
        (normalized_datetime, error) - error is None if valid
    """
    if not datetime_str:
        return None, None

    if "/" not in datetime_str:
        return None, f"Invalid datetime format: expected 'start/end' but got '{datetime_str}'"

    parts = datetime_str.split("/")
    if len(parts) != 2:
        return None, "Invalid datetime format: expected exactly one '/' separator"

    start, end = parts[0].strip(), parts[1].strip()

    # Validate each part is parseable as ISO date
    iso_pattern = r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})?)?$"
    for part, label in [(start, "start"), (end, "end")]:
        if not re.match(iso_pattern, part):
            return (
                None,
                f"Invalid {label} date: expected ISO-8601 format (e.g., '2021-10-01' or '2021-10-01T00:00:00Z') but got '{part}'",
            )

    return f"{start}/{end}", None
