# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.logger import logger
from githubkit.webhooks import parse
from githubkit.webhooks.models import InstallationLite
from githubkit.webhooks.types import WebhookEvent
from pydantic import ValidationError

from insights.api import GlobalStateDep, InsightsDep
from insights.engine.handlers import handle_webhook
from insights.eventdb import EventDB

router = APIRouter(prefix="/github", tags=["github"])


def get_installation_id(event: WebhookEvent) -> int:
    installation: InstallationLite | None = getattr(event, "installation")
    if installation is None:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Installation not specified",
        )
    return installation.id


@router.post("/hooks")
async def receive_webhook(
    request: Request, gstate: GlobalStateDep, insights: InsightsDep
):
    event_name: str | None = request.headers.get("X-GitHub-Event")
    if event_name is None:
        # not a github webhook event
        return

    assert gstate.inited
    assert gstate.config is not None

    eventdb = EventDB(gstate.config)

    try:
        event: WebhookEvent = parse(event_name, await request.body())
        logger.debug(f"Event received: {event_name}, type: {type(event)}")
    except ValidationError as e:
        logger.error(f"Unable to parse incoming event '{event_name}': {str(e)}")
        await eventdb.webhook_error(request, msg=str(e))
        return

    await eventdb.webhook(request)

    installation_id = get_installation_id(event)
    installation = await insights.get_installation(installation_id)

    await handle_webhook(event, event_name, insights, installation)
