# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from fastapi import APIRouter, Request
from fastapi.logger import logger
from githubkit.webhooks import parse
from githubkit.webhooks.types import WebhookEvent

from insights.engine.handlers import handle_webhook

router = APIRouter(prefix="/github", tags=["github"])


@router.post("/hooks")
async def receive_webhook(request: Request):
    event_name: str | None = request.headers.get("X-GitHub-Event")
    if event_name is None:
        # not a github webhook event
        return

    event: WebhookEvent = parse(event_name, await request.body())
    logger.debug(
        f"event received: {event_name}, event: {event.model_dump_json(indent=2)}"
    )

    await handle_webhook(event_name, event)
