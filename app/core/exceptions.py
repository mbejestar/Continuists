"""
Continuum Platform Domain Exceptions & Error Hierarchy.

Written with explicit domain boundary handling:
- Distinguishes between authorization (authentication/token failure) vs access permission
- Enforces explicit legal & regulatory exceptions (POPIA data subject violations,
  unauthorized estate succession claims under SA Administration of Estates Act)
- Enforces financial & quota limits without exposing internal stack traces.
"""

from typing import Optional, Dict, Any

class ContinuumBaseException(Exception):
    """Base exception for all Continuum domain-specific failures."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class StorageQuotaExceededError(ContinuumBaseException):
    """
    Raised when a user on the Free tier attempts to exceed the 50 MB
    cumulative storage cap per Mission, or when an individual file exceeds
    the infrastructure threshold.
    """
    def __init__(self, current_bytes: int, incoming_bytes: int, limit_bytes: int):
        current_mb = current_bytes / (1024 * 1024)
        incoming_mb = incoming_bytes / (1024 * 1024)
        limit_mb = limit_bytes / (1024 * 1024)
        msg = (
            f"Mission storage quota exceeded. Current: {current_mb:.2f}MB, "
            f"attempting to upload {incoming_mb:.2f}MB, exceeding the {limit_mb:.0f}MB free tier limit. "
            f"Continuum Premium (R100/mo) unlocks unlimited mission storage."
        )
        super().__init__(msg, {
            "current_bytes": current_bytes,
            "incoming_bytes": incoming_bytes,
            "limit_bytes": limit_bytes,
            "upgrade_url": "/api/settings/premium/upgrade"
        })


class ConfidentialityLeakagePreventionError(ContinuumBaseException):
    """
    CRITICAL SECURITY EXCEPTION:
    Triggered if an internal service attempts to serialize unmasked findings,
    lessons learned, or proprietary calculation files to a non-purchaser.
    """
    def __init__(self, mission_id: str, field_name: str):
        super().__init__(
            f"Server-side redaction guard blocked attempt to leak field '{field_name}' for mission {mission_id}.",
            {"mission_id": mission_id, "field": field_name}
        )


class OwnershipDeclarationMissingError(ContinuumBaseException):
    """
    Raised when an owner attempts to list a Mission on the marketplace
    without completing the mandatory 7-point IP & employment declaration.
    """
    def __init__(self, mission_id: str):
        super().__init__(
            "An immutable Ownership & IP Rights Declaration must be executed before marketplace submission.",
            {"mission_id": mission_id, "required_action": "POST /api/missions/{id}/ownership-declaration"}
        )


class UnauthorizedSuccessionClaimError(ContinuumBaseException):
    """
    Raised when an unauthorized party attempts to claim management or proceeds
    of an inactive mission without statutory Master of the High Court Letters of Executorship.
    """
    def __init__(self, mission_id: str, claimant_id: str):
        super().__init__(
            "Nominated emergency contact does not hold legal estate title. "
            "Master of the High Court verification required under SA Administration of Estates Act 66 of 1965.",
            {"mission_id": mission_id, "claimant_id": claimant_id}
        )
