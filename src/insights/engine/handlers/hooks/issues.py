# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from fastapi.logger import logger
from githubkit.webhooks.types import IssueCommentEvent

from insights.engine.insights import Insights
from insights.engine.installation import Installation


async def handle_issue_comment(
    insights: Insights, installation: Installation, event: IssueCommentEvent
):
    logger.debug(f"issue comment, action: '{event.action}'")
    logger.debug(f"installation: {event.installation}")

    issue_id = event.issue.node_id
    await installation.handle_issue_comment(issue_id, event)
