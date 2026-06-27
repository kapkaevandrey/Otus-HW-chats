from __future__ import annotations

from http import HTTPStatus
from string import ascii_letters, ascii_uppercase, digits
from typing import Any

import jwt
from pydantic import ValidationError

from app.core.services.utils import ServiceUtils
from app.exceptions import BaseServiceError
from app.schemas.services import (
    AuthCheckTokenData,
    UserTokenData,
)


class AuthUtils(ServiceUtils):
    PASSWORD_MISMATCH_ERROR = "Password mismatch"
    WRONG_PASSWORD = "Не верное значение пароля"
    DEFAULT_AVAILABLE_SYMBOLS = set(ascii_letters + digits + ",.%$@-")
    DEFAULT_NEED_SYMBOLS = [set(ascii_uppercase), set(",.%$@-"), set(digits)]
    USER_NOT_AUTHORIZED_MESSAGE = "User is not authorized"
    WRONG_TOKEN_TYPE_MESSAGE = "Wrong token type"
    TOKEN_REQUIRED_MESSAGE = "Token required"
    INVALID_TOKEN_FORMAT_MESSAGE = "Invalid token format {error}"
    INVALID_JWT_TOKEN_MESSAGE = "Invalid JWT token"
    INVALID_JWT_PAYLOAD_MESSAGE = "Invalid JWT payload"
    INVALID_JWT_SCOPE_MESSAGE = "Invalid JWT scope"
    INVALID_TOKEN_SCHEMA_MESSAGE = "Token or scheme is not valid"

    def get_user_data_from_jwt(self, jwt_token: str, alg: str, secret: str | None) -> UserTokenData:
        payload = self._get_jwt_payload(jwt_token, alg, secret)
        try:
            return UserTokenData.model_validate(payload)
        except ValidationError as error:
            self.logger.error(self.INVALID_JWT_PAYLOAD_MESSAGE)
            raise BaseServiceError(
                status=HTTPStatus.UNAUTHORIZED,
                error_message=self.INVALID_JWT_PAYLOAD_MESSAGE,
                error_details={"errors": error.errors()},
            ) from error

    def _get_jwt_payload(self, jwt_token: str, alg: str, secret: str | None) -> dict:
        decode_params: dict[str, Any] = {"key": secret} if secret else {"options": {"verify_signature": False}}
        try:
            decode_params["algorithms"] = alg
            payload = jwt.decode(jwt_token, **decode_params)
            return payload
        except jwt.InvalidTokenError as error:
            error_message = self.INVALID_TOKEN_FORMAT_MESSAGE.format(error=error)
            self.logger.error(error_message)
            raise BaseServiceError(status=HTTPStatus.UNAUTHORIZED, error_message=error_message) from error

    def get_token_for_headers(self, headers: dict[str, str], auth_info: AuthCheckTokenData) -> str:
        raw_token = None
        header_key = auth_info.header_key.strip().lower()
        for key, value in headers.items():
            if key.strip().lower() == header_key:
                raw_token = value
                break
        if not raw_token or not isinstance(raw_token, str):
            raise BaseServiceError(status=HTTPStatus.UNAUTHORIZED, error_message=self.INVALID_JWT_TOKEN_MESSAGE)
        scheme, *token_parts = raw_token.split(" ", 1)
        if scheme != auth_info.token_type or not token_parts:
            raise BaseServiceError(status=HTTPStatus.UNAUTHORIZED, error_message=self.INVALID_TOKEN_SCHEMA_MESSAGE)
        return token_parts[0]
