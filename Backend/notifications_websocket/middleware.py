"""=============================================================================
WEBSOCKET JWT AUTHENTICATION MIDDLEWARE
=============================================================================
Authenticates WebSocket connections using JWT tokens from query string.
Extracts the token, validates it, and attaches the user to the scope.
=============================================================================
"""

import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token: str):
    """Validate JWT token and return the associated user.

    Uses the same JWT configuration as the REST framework (simplejwt).

    Args:
        token: JWT access token string

    Returns:
        User instance if token is valid, AnonymousUser otherwise

    """
    try:
        from rest_framework_simplejwt.authentication import JWTAuthentication
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

        jwt_auth = JWTAuthentication()

        # Validate and decode the token
        validated_token = jwt_auth.get_validated_token(token)
        user_id = validated_token.get("user_id")

        if not user_id:
            logger.warning("WebSocket JWT token missing user_id claim")
            return AnonymousUser()

        user = User.objects.filter(id=user_id).first()
        if user is None:
            logger.warning(
                "WebSocket JWT token references non-existent user_id: %s",
                user_id,
            )
            return AnonymousUser()

        return user

    except (TokenError, InvalidToken) as e:
        logger.warning("WebSocket JWT token validation failed: %s", e)
        return AnonymousUser()
    except Exception as e:
        logger.error("Unexpected error during WebSocket JWT authentication: %s", e)
        return AnonymousUser()


class JWTAuthMiddleware:
    """Custom middleware for authenticating WebSocket connections via JWT.

    Expects the JWT token in the query string as:
        ws://host/ws/notifications/token=<jwt_token>

    The authenticated user is attached to scope['user'].
    """

    def __init__(self, app):
        """Init"""
        self.app = app

    async def __call__(self, scope, receive, send):
        """Call"""
        # Parse query string
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)

        # Extract token from query string
        token_list = query_params.get("token", [])
        token = token_list[0] if token_list else None

        if token:
            scope["user"] = await get_user_from_token(token)
        else:
            # Also check headers as fallback (Authorization: Bearer <token>)
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode("utf-8")

            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                scope["user"] = await get_user_from_token(token)
            else:
                scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)


class JWTAuthMiddlewareStrict(JWTAuthMiddleware):
    """Strict version that rejects connections without valid JWT tokens.

    Use this for production environments where unauthenticated
    WebSocket connections should not be allowed.
    """

    async def __call__(self, scope, receive, send):
        """Call"""
        # Parse query string
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)

        # Extract token from query string
        token_list = query_params.get("token", [])
        token = token_list[0] if token_list else None

        # Fallback: check Authorization header
        if not token:
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode("utf-8")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]

        if not token:
            logger.warning("WebSocket connection rejected: no JWT token provided")
            await send(
                {
                    "type": "websocket.close",
                    "code": 4001,  # Custom close code: unauthorized
                },
            )
            return None

        user = await get_user_from_token(token)

        if user.is_anonymous:
            logger.warning("WebSocket connection rejected: invalid JWT token")
            await send(
                {
                    "type": "websocket.close",
                    "code": 4001,
                },
            )
            return None

        scope["user"] = user
        return await self.app(scope, receive, send)
