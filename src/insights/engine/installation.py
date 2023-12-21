# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import motor.motor_asyncio

_DB_COLLECTION_PROJECTS = "projects"
_DB_COLLECTION_PROJECT_BY_ID = "project.{project_id}"
_DB_COLLECTION_COMMENTS = "comments"
_DB_COLLECTION_ISSUES = "issues"


class Installation:
    _db: motor.motor_asyncio.AsyncIOMotorDatabase

    def __init__(self, db: motor.motor_asyncio.AsyncIOMotorDatabase) -> None:
        self._db = db

    async def init(self) -> None:
        await self._db.create_collection(_DB_COLLECTION_PROJECTS)
        await self._db.create_collection(_DB_COLLECTION_ISSUES)
        await self._db.create_collection(_DB_COLLECTION_COMMENTS)
