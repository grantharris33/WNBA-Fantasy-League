import json
from copy import deepcopy
from datetime import datetime
from typing import Callable, Dict, Optional, Union

import jsonpatch
from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.database import get_db
from app.core.security import ALGORITHM
from app.models import TransactionLog, User


class ChangeLogMiddleware(BaseHTTPMiddleware):
    """Middleware that captures database differences for mutating operations."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.mutating_methods = {"POST", "PUT", "DELETE", "PATCH"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip for GET and other non-mutating requests
        if request.method not in self.mutating_methods:
            return await call_next(request)

        # Extract user ID from token, if available
        user_id = await self._get_user_id_from_request(request)

        # Capture route path for logging
        path = request.url.path

        # Process the request first
        response = await call_next(request)

        # Only log successful mutations (2xx responses)
        if 200 <= response.status_code < 300:
            # Use a separate session for logging to avoid transaction conflicts
            from app.core.database import SessionLocal

            db = SessionLocal()
            try:
                # Create a log entry with the basic info
                log_entry = TransactionLog(
                    user_id=user_id,
                    path=path,
                    method=request.method,
                    action=f"{request.method} {path}",
                    timestamp=datetime.utcnow(),
                    # Additional diff information would be added here in a real implementation
                    patch=None,  # Placeholder for JSONPatch
                )

                db.add(log_entry)
                db.commit()
            except SQLAlchemyError:
                # Don't fail the request if logging fails
                db.rollback()
            finally:
                db.close()

        return response

    async def _get_user_id_from_request(self, request: Request) -> Optional[int]:
        """Extract the user ID from the JWT token in the request."""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                return None
            return int(user_id)
        except (JWTError, ValueError):
            return None


def serialize_model(model) -> dict:
    """Convert a SQLAlchemy model to a dictionary for diffing."""
    if not model:
        return {}

    result = {}
    for column in model.__table__.columns:
        value = getattr(model, column.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        result[column.name] = value

    return result


def compute_json_patch(before: dict, after: dict) -> str:
    """Compute a JSONPatch between two JSON objects."""
    patch = jsonpatch.make_patch(before, after)
    return json.dumps(patch.patch)


def diff_models(before_model, after_model) -> str:
    """Compute a diff between two model instances."""
    before = serialize_model(before_model)
    after = serialize_model(after_model)
    return compute_json_patch(before, after)
