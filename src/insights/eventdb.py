# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import json
from datetime import datetime as dt
from pathlib import Path
from typing import Any, Literal

import githubkit as ghk
from fastapi import Request
from fastapi.logger import logger
from pydantic import BaseModel

from insights.config import Config, EventDBConfigModel


class _LogEntry(BaseModel):
    event: bool
    error: bool


_EventType = Literal["webhook", "rest"]


class EventDB:
    _config: EventDBConfigModel | None
    _path: Path | None
    _event_type: dict[_EventType, _LogEntry]

    def __init__(self, config: Config) -> None:
        self._config = config.eventdb
        self._path = self._config.path if self._config is not None else None
        self._event_type = {
            "webhook": _LogEntry(
                event=self._log_webhook,
                error=self._log_webhook_errors,
            ),
            "rest": _LogEntry(
                event=self._log_rest,
                error=self._log_rest_errors,
            ),
        }

    @property
    def _log_webhook(self) -> bool:
        return self._config is not None and self._config.log_webhook

    @property
    def _log_webhook_errors(self) -> bool:
        return self._config is not None and self._config.log_webhook_errors

    @property
    def _log_rest(self) -> bool:
        return self._config is not None and self._config.log_rest

    @property
    def _log_rest_errors(self) -> bool:
        return self._config is not None and self._config.log_rest_errors

    def _get_event_path(self, event_type: _EventType, is_error: bool) -> Path | None:
        if self._config is None:
            return None

        if event_type not in self._event_type:
            return None

        if not (  # check if we should log
            self._event_type[event_type].error
            if is_error
            else self._event_type[event_type].event
        ):
            return None

        log_type = "error" if is_error else "event"

        path = self._config.path.joinpath(event_type, log_type)
        if not path.exists():
            path.mkdir(parents=True)

        event_dt = dt.utcnow().isoformat()
        filename = f"{event_type}-{log_type}-{event_dt}.json"
        return path.joinpath(filename)

    async def _log_webhook_event(
        self,
        request: Request,
        *,
        is_error: bool,
        msg: str | None = None,
    ) -> None:
        event_file = self._get_event_path("webhook", is_error)
        if event_file is None:
            return

        event_name: str | None = request.headers.get("X-GitHub-Event")
        if event_name is None:
            logger.error("Can't log non-event")
            return

        event_body = await request.json()
        headers_lst = request.headers.items()
        event_entry: dict[str, Any] = {
            "event_name": event_name,
            "event": {"headers": headers_lst, "payload": event_body},
            "msg": msg,
        }

        with event_file.open("+w") as fp:
            json.dump(event_entry, fp, indent=2)

        error_event = "error " if is_error else ""
        logger.debug(f"Wrote {error_event}event type '{event_name}' to eventdb")

    async def webhook(self, request: Request) -> None:
        await self._log_webhook_event(request, is_error=False, msg=None)

    async def webhook_error(self, request: Request, msg: str | None = None) -> None:
        await self._log_webhook_event(request, is_error=True, msg=msg)

    async def _log_rest_event(
        self,
        response: ghk.Response[Any],
        *,
        call_name: str,
        is_error: bool,
        msg: str | None = None,
    ) -> None:
        event_file = self._get_event_path("rest", is_error)
        if event_file is None:
            return

        event_body = response.json()
        headers_lst = list(response.headers.items())
        event_entry: dict[str, Any] = {
            "event_name": call_name,
            "event": {"headers": headers_lst, "payload": event_body},
            "msg": msg,
        }

        with event_file.open("+w") as fp:
            json.dump(event_entry, fp, indent=2)

        error_event = "error " if is_error else ""
        logger.debug(f"Wrote {error_event}event type '{call_name}' to eventdb")

    async def rest(self, response: Any, *, call_name: str) -> None:
        await self._log_rest_event(
            response, call_name=call_name, is_error=False, msg=None
        )

    async def rest_error(
        self, response: Any, *, call_name: str, msg: str | None = None
    ) -> None:
        await self._log_rest_event(
            response, call_name=call_name, is_error=True, msg=msg
        )
