"""Text formatting module."""


def to_uppercase(text: str) -> str:
    """Convert text to uppercase.

    Args:
        text: Input string to convert.

    Returns:
        The input string converted to uppercase.
    """
    return text.upper()


def to_lowercase(text: str) -> str:
    """Convert text to lowercase.

    Args:
        text: Input string to convert.

    Returns:
        The input string converted to lowercase.
    """
    return text.lower()


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to a maximum length with an optional suffix.

    Args:
        text: Input string to truncate.
        max_length: Maximum length of the resulting string (including suffix).
        suffix: String appended to truncated text. Defaults to "...".

    Returns:
        The original text if it fits within max_length, otherwise the
        truncated text with the suffix appended.

    Raises:
        ValueError: If max_length is less than the length of suffix.
    """
    if len(text) <= max_length:
        return text
    if max_length < len(suffix):
        raise ValueError(f"max_length ({max_length}) must be >= len(suffix) ({len(suffix)})")
    return text[: max_length - len(suffix)] + suffix
