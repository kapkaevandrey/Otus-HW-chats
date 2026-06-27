from __future__ import annotations


class RetriesExceededError(Exception):
    """Exception means that number of attempts to process message exceeded max
    times."""


class ImproperlyConfiguratedError(ValueError):
    """Exception means that there is incorrect parameters passed to extractor
    or consumer."""
