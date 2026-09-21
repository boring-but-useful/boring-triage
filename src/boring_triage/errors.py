"""Public exceptions for fixture and evidence-tool failures."""


class BoringTriageError(Exception):
    """Base class for expected application failures."""


class FixtureError(BoringTriageError):
    """Raised when a case fixture is missing, malformed, or unsafe."""


class QueryError(BoringTriageError):
    """Raised when an evidence query violates the case contract."""


class EvidenceNotFoundError(BoringTriageError):
    """Raised when a requested evidence or resource ID is unknown."""
