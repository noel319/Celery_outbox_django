from typing import Any, Protocol

import structlog
from django.db import transaction

from core.base_model import Model


class UseCaseRequest(Model):
    pass


class UseCaseResponse(Model):
    result: Any = None
    error: str = ''


class UseCase(Protocol):
    def execute(self, request: UseCaseRequest) -> UseCaseResponse:
        with structlog.contextvars.bound_contextvars(
            **self._get_context_vars(request),
        ):
            return self._execute(request)

    def _get_context_vars(self, request: UseCaseRequest) -> dict[str, Any]:  # noqa: ARG002
        """
        !!! WARNING:
            This method is calling out of transaction so do not make db
            queries in this method.
        """
        return {
            'use_case': self.__class__.__name__,
        }

    @transaction.atomic()
    def _execute(self, request: UseCaseRequest) -> UseCaseResponse:
        raise NotImplementedError()
