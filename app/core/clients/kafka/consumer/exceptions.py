class ConsumerRetriesExceededError(Exception):
    """Exception means that number of attempts to process message exceeded max
    times."""


class ConsumerImproperlyConfigurationError(ValueError):
    """Exception means that there is incorrect parameters passed to extractor
    or consumer."""
