class SalesOptimizerError(Exception):
    """Base exception for expected application failures."""


class DataValidationError(SalesOptimizerError):
    """Input data violates the required contract."""


class FeatureBuildError(SalesOptimizerError):
    """Feature generation could not be completed."""


class ModelArtifactError(SalesOptimizerError):
    """A model artifact is missing, invalid, or incompatible."""


class InventoryOptimizationError(SalesOptimizerError):
    """A replenishment recommendation could not be calculated."""
