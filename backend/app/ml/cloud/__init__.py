"""Cloud Verification package for AICF."""

from backend.app.ml.cloud.copyleaks_adapter import (
    CopyleaksAdapter,
    CopyleaksDetectionResult,
)
from backend.app.ml.cloud.gptzero_adapter import (
    GPTZeroAdapter,
    GPTZeroDetectionResult,
)
from backend.app.ml.cloud.hive_unified import (
    UnifiedHiveAdapter,
    UnifiedHiveResult,
)
from backend.app.ml.cloud.manager import (
    SUPPORTED_PROVIDERS,
    CloudProviderStatus,
    CloudVerificationManager,
    cloud_manager,
)

__all__ = [
    "cloud_manager",
    "CloudVerificationManager",
    "CloudProviderStatus",
    "SUPPORTED_PROVIDERS",
    "GPTZeroAdapter",
    "GPTZeroDetectionResult",
    "CopyleaksAdapter",
    "CopyleaksDetectionResult",
    "UnifiedHiveAdapter",
    "UnifiedHiveResult",
]
