import re


def slugify(text):
    """Turn a display name into a URL slug."""
    return text.strip().lower().replace(" ", "_")
