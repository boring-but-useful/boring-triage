"""Public exceptions for fixture and evidence-tool failures."""


class BoringTriageError(Exception):
    """Base class for expected application failures."""


class FixtureError(BoringTriageError):
    """Raised when a case fixture is missing, malformed, or unsafe."""


class QueryError(BoringTriageError):
    """Raised when an evidence query violates the case contract."""


class EvidenceNotFoundError(BoringTriageError):
    """Raised when a requested evidence or resource ID is unknown."""


class ApprovalRequiredError(BoringTriageError):
    """Raised when evidence execution lacks approval for the exact saved plan."""


class InvalidModelOutputError(BoringTriageError):
    """Raised when model output violates an application-enforced contract."""


class ModelProviderError(BoringTriageError):
    """Raised when the configured model provider cannot complete a request."""


class ArtifactError(BoringTriageError):
    """Raised when a saved plan or report cannot be read or written safely."""
