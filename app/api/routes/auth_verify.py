"""Stack Auth JWT verification test endpoint.

This module provides a test endpoint for verifying Stack Auth JWT tokens.
This is a basic implementation for testing purposes during Story 0.3.

Full authentication integration will be implemented in Story 1.1, including:
- User session management
- Protected route middleware
- Token refresh logic
- User context extraction
"""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, status
from typing import Dict, Any

from app.core.auth import verify_jwt_token, extract_bearer_token, JWTVerificationError


def create_auth_verify_router() -> APIRouter:
    """Factory function to create the auth verification router.

    Returns:
        Configured APIRouter for auth verification endpoints.
    """
    router = APIRouter(prefix="/api/auth", tags=["authentication"])

    @router.get("/verify")
    async def verify_token(
        authorization: str | None = Header(None, description="Bearer token in Authorization header")
    ) -> Dict[str, Any]:
        """Verify a Stack Auth JWT token.

        This endpoint validates a JWT token issued by Stack Auth and returns
        the decoded payload if valid.

        **Usage:**
        ```bash
        curl -H "Authorization: Bearer <your-jwt-token>" http://localhost:8000/api/auth/verify
        ```

        **Response (Success - 200):**
        ```json
        {
            "status": "valid",
            "message": "Token verified successfully",
            "payload": {
                "sub": "user-id-123",
                "email": "user@example.com",
                "iat": 1234567890,
                "exp": 1234571490
            }
        }
        ```

        **Response (Error - 401):**
        ```json
        {
            "detail": "Invalid token: JWT verification failed: Signature has expired"
        }
        ```

        Args:
            authorization: The Authorization header containing the Bearer token.

        Returns:
            A dictionary containing verification status and decoded token payload.

        Raises:
            HTTPException: 401 Unauthorized if token is missing, invalid, or expired.

        Note:
            This is a test endpoint for Story 0.3. Full authentication middleware
            will be implemented in Story 1.1.
        """
        try:
            # Extract the bearer token from Authorization header
            token = extract_bearer_token(authorization)

            # Verify the token and get the payload
            payload = await verify_jwt_token(token)

            return {
                "status": "valid",
                "message": "Token verified successfully",
                "payload": payload
            }

        except JWTVerificationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @router.get("/health")
    async def auth_health() -> Dict[str, str]:
        """Health check endpoint for auth service.

        Returns:
            A dictionary indicating the auth service health status.
        """
        from app.core.config import get_settings

        settings = get_settings()

        # Check if Stack Auth is configured
        is_configured = bool(settings.stack_auth_project_id)

        return {
            "status": "healthy" if is_configured else "not_configured",
            "service": "stack_auth",
            "message": "Stack Auth is configured" if is_configured else "Stack Auth project ID not configured"
        }

    return router
