# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

PyObjectId = Annotated[str, BeforeValidator(str)]


class ProjectEntry(BaseModel):
    """Container for a single project entry."""

    id: PyObjectId | None = Field(alias="_id", default=None)
    pass


class ProjectsCollection(BaseModel):
    """Collection for all project entries."""

    projects: list[ProjectEntry]
