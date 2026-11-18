from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import httpx
from google.genai._gaos.lib.compat_errors import APIConnectionError, NotFoundError


class SdkErrors:
    """Builds the SDK exceptions the fallback client reacts to, without any HTTP traffic."""

    _REQUEST = httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/interactions")

    @classmethod
    def connection_error(cls) -> APIConnectionError:
        return APIConnectionError(request=cls._REQUEST)

    @classmethod
    def model_not_found(cls) -> NotFoundError:
        response = httpx.Response(404, request=cls._REQUEST)
        return NotFoundError("model not found", response=response, body=None)


def retry_options() -> Any:
    """A stand-in for types.HttpRetryOptions; GeminiClient only passes it through."""
    return SimpleNamespace(attempts=1)
