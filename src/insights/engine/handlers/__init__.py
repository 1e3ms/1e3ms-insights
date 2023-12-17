# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from functools import singledispatch

from fastapi.logger import logger
from githubkit.webhooks.types import IssueCommentEvent, WebhookEvent


@singledispatch
async def handle_webhook(event_name: str, event: WebhookEvent):
    logger.debug(f"got event '{event_name}': {event}")


@handle_webhook.register
async def _(event_name: str, event: IssueCommentEvent):
    logger.debug(f"got issue comment event: {event.action}")
