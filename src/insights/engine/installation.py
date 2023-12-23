# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from datetime import datetime as dt
from typing import Optional, cast

import githubkit.rest.models as ghk_rest_models
import githubkit.webhooks.types as ghk_webhook_types
import motor.motor_asyncio
from fastapi.logger import logger
from githubkit.utils import exclude_unset

from insights.engine.db_types import InstallationCommentEntry, InstallationIssueEntry
from insights.engine.github import Github
from insights.eventdb import EventDB

_DB_COLLECTION_PROJECTS = "projects"
_DB_COLLECTION_PROJECT_BY_ID = "project.{project_id}"
_DB_COLLECTION_COMMENTS = "comments"
_DB_COLLECTION_ISSUES = "issues"


class Installation:
    _id: int
    _db: motor.motor_asyncio.AsyncIOMotorDatabase
    _github: Github
    _eventdb: EventDB

    def __init__(
        self,
        id: int,
        github: Github,
        db: motor.motor_asyncio.AsyncIOMotorDatabase,
        eventdb: EventDB,
    ) -> None:
        self._id = id
        self._db = db
        self._github = github
        self._eventdb = eventdb

    async def init(self) -> None:
        await self._db.create_collection(_DB_COLLECTION_PROJECTS)
        await self._db.create_collection(_DB_COLLECTION_ISSUES)
        await self._db.create_collection(_DB_COLLECTION_COMMENTS)

    async def handle_issue_comment(
        self, issue_id: str, event: ghk_webhook_types.IssueCommentEvent
    ) -> None:
        entry = InstallationCommentEntry(
            issue_id=event.issue.node_id,
            comment_id=event.comment.node_id,
            updated_at=event.comment.updated_at,
            by_login=event.comment.user.login,
            comment=event.comment,
            repository=event.repository,
        )

        coll = self._get_comments_coll()
        new_entry = await coll.insert_one(
            entry.model_dump(by_alias=True, exclude=set("id"), exclude_unset=True)
        )
        logger.debug(
            f"Inserted new entry for comment '{entry.comment_id},"
            f" issue '{entry.issue_id}': {new_entry.inserted_id}"
        )

        await self._maybe_add_issue(
            event.repository.owner.login,
            event.repository.name,
            event.issue.number,
            event.issue.node_id,
        )

    def _get_comments_coll(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self._db.get_collection(_DB_COLLECTION_COMMENTS)

    def _get_issues_coll(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self._db.get_collection(_DB_COLLECTION_ISSUES)

    async def _maybe_add_issue(
        self,
        repo_owner: str,
        repo_name: str,
        issue_number: int,
        issue_id: str | None = None,
    ) -> None:
        if issue_id is not None:
            coll = self._get_issues_coll()
            entry: InstallationIssueEntry | None = cast(
                Optional[InstallationIssueEntry],
                await coll.find_one({"issue_id": issue_id}),
            )
            if entry is not None:
                return

        await self._fetch_issue(repo_owner, repo_name, issue_number)

    async def _fetch_issue(
        self, repo_owner: str, repo_name: str, issue_number: int
    ) -> None:
        gh = self._github.get(self._id)
        response = await gh.rest.issues.async_get(repo_owner, repo_name, issue_number)
        issue: ghk_rest_models.Issue = response.parsed_data

        await self._eventdb.rest(response, call_name="fetch_issue")

        labels: list[str] = []
        for label in issue.labels:
            if isinstance(label, str):
                labels.append(label)
                continue
            name: str | None = exclude_unset(label.name)
            if name is not None:
                labels.append(name)

        entry = InstallationIssueEntry(
            issue_id=issue.node_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            issue_number=issue.number,
            fetched_at=dt.utcnow(),
            events=[],
            labels=labels,
            milestone=issue.milestone,
            state=issue.state,
            instance=issue,
        )

        coll = self._get_issues_coll()
        new_entry = await coll.insert_one(
            entry.model_dump(by_alias=True, exclude=set("id"), exclude_unset=True)
        )
        logger.debug(
            f"inserted new entry for issue '{entry.issue_id}': {new_entry.inserted_id}"
        )
