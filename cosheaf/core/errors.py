"""Core domain exceptions."""


class CosheafCoreError(ValueError):
    """Base error for core artifact model helpers."""


class ArtifactIdError(CosheafCoreError):
    """Raised when an artifact ID does not match the required format."""
