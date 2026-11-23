"""Pydantic schemas for the Cloud Verification Hub."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CloudProviderStatusResponse(BaseModel):
    """Status card for an authorized third-party cloud verification provider."""

    provider: str
    name: str
    description: str
    supported_types: list[str]
    is_configured: bool
    source: str
    masked_key: str
    api_connection_status: str
    last_tested_at: datetime | None = None
    last_test_status: str | None = None
    last_test_message: str | None = None
    doc_url: str

    model_config = ConfigDict(from_attributes=True)


class SaveCloudCredentialRequest(BaseModel):
    """Payload to securely store or update a cloud API key."""

    provider: str = Field(..., description="Provider identifier: hive, gptzero, or copyleaks")
    api_key: str = Field(..., min_length=4, max_length=256, description="Plain API key (will be encrypted immediately)")


class TestCloudConnectionRequest(BaseModel):
    """Payload to test connection to a third-party provider."""

    provider: str
    api_key: str | None = None


class CloudOperationResponse(BaseModel):
    """Generic status response for credential and test operations."""

    success: bool
    message: str
    provider: str


class CloudTextVerificationRequest(BaseModel):
    """Request for running optional cloud verification on text."""

    text: str = Field(..., min_length=10)
    user_consent: bool = Field(..., description="Mandatory explicit analyst consent to transmit payload externally")
    providers: list[str] | None = None


class CloudProviderResultItem(BaseModel):
    """Outcome from an individual cloud provider verification."""

    is_configured: bool
    status: str
    ai_score: float | None = None
    human_score: float | None = None
    error_message: str | None = None


class CloudTextVerificationResponse(BaseModel):
    """Consolidated outcome from cloud verification."""

    consent_granted: bool
    results: dict[str, CloudProviderResultItem] = Field(default_factory=dict)
    error: str | None = None
