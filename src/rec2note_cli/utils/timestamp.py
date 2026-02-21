"""Parse SRT-style timestamps (HH:MM:SS or HH:MM:SS,mmm) to seconds."""

import re


def timestamp_to_seconds(s: str) -> int:
    """
    Convert a timestamp string to whole seconds.

    Accepts:
        - HH:MM:SS (e.g. "01:30:45")
        - HH:MM:SS,mmm (e.g. "01:30:45,123" — milliseconds are truncated)

    Returns:
        Total seconds (int). Returns 0 for empty or unparseable input.
    """
    if not s or not s.strip():
        return 0
    s = s.strip()
    # HH:MM:SS or HH:MM:SS,mmm
    match = re.match(r"^(\d+):(\d{1,2}):(\d{1,2})(?:[,.](\d+))?$", s)
    if not match:
        return 0
    h, m, sec, ms = match.groups()
    h, m, sec = int(h), int(m), int(sec)
    return h * 3600 + m * 60 + sec
