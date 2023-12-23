# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from datetime import datetime as dt
from typing import Annotated, Any

import githubkit.rest.models as ghk_rest_models
import githubkit.webhooks.models as ghk_wh_models
from pydantic import BaseModel, BeforeValidator, Field

from insights.error import InsightsError


class DBError(InsightsError):
    def __init__(self, msg: str | None = None) -> None:
        super().__init__(f"Database Error: {msg}")


PyObjectId = Annotated[str, BeforeValidator(str)]


class InstallationEntry(BaseModel):
    id: PyObjectId | None = Field(alias="_id", default=None)

    installation_id: int
    updated_at: dt | None = Field(default=None)
    probed_at: dt | None = Field(default=None)
    deleted_at: dt | None = Field(default=None)


class InstallationCommentEntry(BaseModel):
    id: PyObjectId | None = Field(alias="_id", default=None)

    issue_id: str
    comment_id: str
    updated_at: dt
    by_login: str
    comment: ghk_wh_models.IssueComment
    repository: ghk_wh_models.Repository


class InstallationIssueEntry(BaseModel):
    id: PyObjectId | None = Field(alias="_id", default=None)

    issue_id: str
    repo_owner: str
    repo_name: str
    issue_number: int

    fetched_at: dt

    events: list[Any] = Field(default=[])
    labels: list[str] = Field(default=[])
    milestone: ghk_rest_models.Milestone | None
    state: str

    instance: ghk_rest_models.Issue


class ProjectEntry(BaseModel):
    """Container for a single project entry."""

    id: PyObjectId | None = Field(alias="_id", default=None)
    pass


class ProjectsCollection(BaseModel):
    """Collection for all project entries."""

    projects: list[ProjectEntry]
