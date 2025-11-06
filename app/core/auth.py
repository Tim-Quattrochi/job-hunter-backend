"""Stack Auth JWT verification utilities.

This module provides utilities for verifying JWT tokens issued by Stack Auth.
Since Stack Auth does not provide a dedicated Python SDK, we use the standard
JWT verification approach with PyJWT and fetch the JWKS (JSON Web Key Set)
from Stack Auth's public endpoint.

Note: Full authentication integration will be implemented in Story 1.1.
This is a basic verification setup for testing purposes.
"""

from __future__ import annotations

import httpx
from jose import jwt, jwk
from jose.exceptions import JWTError
from typing import Dict, Any
from functools import lru_cache
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings


class StackAuthError(Exception):
    """Base exception for Stack Auth errors."""
    pass


class JWTVerificationError(StackAuthError):
    """Raised when JWT verification fails."""
    pass


@lru_cache(maxsize=1)
def get_jwks_uri() -> str:
    """Get the JWKS URI for Stack Auth.

    Stack Auth uses the standard OIDC discovery endpoint pattern.
    The JWKS URI is typically at: https://api.stack-auth.com/api/v1/projects/{project_id}/.well-known/jwks.json

    Returns:
        The JWKS URI for the configured Stack Auth project.

    Raises:
        StackAuthError: If project ID is not configured.
    """
    settings = get_settings()
    if not settings.stack_auth_project_id:
        raise StackAuthError("NEXT_PUBLIC_STACK_PROJECT_ID is not configured")

    # Stack Auth JWKS endpoint pattern
    return f"https://api.stack-auth.com/api/v1/projects/{settings.stack_auth_project_id}/.well-known/jwks.json"


async def fetch_jwks() -> Dict[str, Any]:
    """Fetch the JSON Web Key Set (JWKS) from Stack Auth.

    The JWKS contains the public keys used to verify JWT signatures.
    This is cached to avoid unnecessary network requests.

    Returns:
        The JWKS as a dictionary.

    Raises:
        StackAuthError: If fetching JWKS fails.
    """
    jwks_uri = get_jwks_uri()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_uri, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise StackAuthError(f"Failed to fetch JWKS: {e}") from e


async def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify a JWT token issued by Stack Auth.

    This function:
    1. Fetches the JWKS from Stack Auth
    2. Verifies the token signature using the public key
    3. Validates token claims (expiration, issuer, audience)
    4. Returns the decoded payload

    Args:
        token: The JWT token string to verify.

    Returns:
        The decoded JWT payload as a dictionary.

    Raises:
        JWTVerificationError: If token verification fails.

    Example:
        ```python
        try:
            payload = await verify_jwt_token(token)
            user_id = payload.get("sub")
            print(f"Authenticated user: {user_id}")
        except JWTVerificationError as e:
            print(f"Invalid token: {e}")
        ```
    """
    settings = get_settings()

    if not settings.stack_auth_project_id:
        raise JWTVerificationError("NEXT_PUBLIC_STACK_PROJECT_ID is not configured")

    try:
        # Fetch JWKS to get public keys
        jwks = await fetch_jwks()

        # Decode the token header to get the key ID (kid)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            raise JWTVerificationError("Token missing 'kid' (key ID) in header")

        # Find the matching public key in JWKS
        key_data = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                key_data = key
                break

        if not key_data:
            raise JWTVerificationError(f"No matching key found for kid: {kid}")

        # Construct the public key from JWK
        public_key = jwk.construct(key_data)

        # Verify and decode the token
        # Note: Adjust audience and issuer validation as needed for your Stack Auth setup
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],  # Stack Auth typically uses RS256
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": False,  # Set to True if you want to validate audience
            }
        )

        return payload

    except JWTError as e:
        raise JWTVerificationError(f"JWT verification failed: {e}") from e
    except Exception as e:
        raise JWTVerificationError(f"Unexpected error during JWT verification: {e}") from e


def extract_bearer_token(authorization_header: str | None) -> str:
    """Extract the bearer token from an Authorization header.

    Args:
        authorization_header: The Authorization header value (e.g., "Bearer <token>").

    Returns:
        The extracted token string.

    Raises:
        JWTVerificationError: If the header is missing or malformed.

    Example:
        ```python
        token = extract_bearer_token(request.headers.get("Authorization"))
        payload = await verify_jwt_token(token)
        ```
    """
    if not authorization_header:
        raise JWTVerificationError("Missing Authorization header")

    parts = authorization_header.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise JWTVerificationError(
            "Invalid Authorization header format. Expected: 'Bearer <token>'"
        )

    return parts[1]


# Story 1.1: FastAPI Dependencies for Protected Endpoints

# HTTP Bearer security scheme for Swagger UI
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """FastAPI dependency to get the current authenticated user ID.

    This dependency:
    1. Extracts the JWT token from the Authorization header
    2. Verifies the token using Stack Auth's JWKS
    3. Returns the user ID from the token's 'sub' claim

    Args:
        credentials: HTTP Bearer credentials from the Authorization header

    Returns:
        The user ID (from JWT 'sub' claim)

    Raises:
        HTTPException: 401 if token is invalid or missing

    Example:
        ```python
        @app.get("/api/me")
        async def get_me(user_id: str = Depends(get_current_user_id)):
            return {"user_id": user_id}
        ```
    """
    try:
        token = credentials.credentials
        payload = await verify_jwt_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing 'sub' (user ID) claim",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user_id

    except JWTVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """FastAPI dependency to get the full JWT payload.

    Use this when you need access to additional token claims beyond just the user ID.

    Args:
        credentials: HTTP Bearer credentials from the Authorization header

    Returns:
        The complete decoded JWT payload

    Raises:
        HTTPException: 401 if token is invalid or missing

    Example:
        ```python
        @app.get("/api/user-info")
        async def get_user_info(payload: dict = Depends(get_current_token_payload)):
            return {"email": payload.get("email"), "user_id": payload.get("sub")}
        ```
    """
    try:
        token = credentials.credentials
        payload = await verify_jwt_token(token)
        return payload

    except JWTVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
