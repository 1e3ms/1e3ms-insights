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
from typing import Any

from fastapi import APIRouter, Request
from fastapi.logger import logger
from githubkit.webhooks import parse
from githubkit.webhooks.types import WebhookEvent
from pydantic import ValidationError

from insights.config import Config
from insights.engine.handlers import handle_webhook

router = APIRouter(prefix="/github", tags=["github"])


def _get_event_path(config: Config, is_error: bool) -> Path | None:
    ep = config.eventdb if not is_error else config.eventdb_errors
    if ep is not None:
        if not ep.exists():
            ep.mkdir(parents=True)

        event_dt = dt.utcnow().isoformat()
        event_file = ep.joinpath(f"{event_dt}.json")
        return event_file
    return None


async def _maybe_store_event(request: Request, event: WebhookEvent) -> None:
    cfg: Config = request.app.state.config
    event_file = _get_event_path(cfg, False)
    if event_file is None:
        return

    event_dict = await request.json()
    headers_lst = request.headers.items()
    event_entry: dict[str, Any] = {
        "headers": headers_lst,
        "event": event_dict,
    }

    with event_file.open("+a") as fp:
        json.dump(event_entry, fp, indent=2)

    logger.debug(f"Wrote event '{type(event)}' to eventdb at '{event_file}'")


async def _maybe_log_event_error(event_name: str, request: Request, msg: str) -> None:
    cfg: Config = request.app.state.config
    event_file = _get_event_path(cfg, True)
    if event_file is None:
        logger.debug("Not logging error, eventdb error path not set.")
        return

    headers_lst = request.headers.items()
    event_body = await request.json()
    event_entry: dict[str, Any] = {
        "event": {"headers": headers_lst, "payload": event_body},
        "event_name": event_name,
        "error_msg": msg,
    }

    with event_file.open("+a") as fp:
        json.dump(event_entry, fp, indent=2)

    logger.error(f"Wrote event error '{event_name}' to eventdb error at '{event_file}'")


@router.post("/hooks")
async def receive_webhook(request: Request):
    event_name: str | None = request.headers.get("X-GitHub-Event")
    if event_name is None:
        # not a github webhook event
        return

    try:
        event: WebhookEvent = parse(event_name, await request.body())
        logger.debug(f"Event received: {event_name}")
    except ValidationError as e:
        logger.error(f"Unable to parse incoming event '{event_name}': {str(e)}")
        await _maybe_log_event_error(event_name, request, str(e))
        return

    await _maybe_store_event(request, event)

    await handle_webhook(event_name, event)
