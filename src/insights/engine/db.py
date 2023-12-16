# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from urllib.parse import quote_plus

import motor.motor_asyncio

from insights.config import MongoDBConfigModel

_DB_PROJECTS = "projects"
_DB_COLLECTION_PROJECT = "project-{projectid}"


class DBError(Exception):
    _msg: str | None

    def __init__(self, msg: str | None = None) -> None:
        self._msg = msg

    def __str__(self) -> str:
        return f"Database Error: {self._msg}"

    def __repr__(self) -> str:
        return str(self)


class DB:
    _client: motor.motor_asyncio.AsyncIOMotorClient
    _projects_db: motor.motor_asyncio.AsyncIOMotorDatabase

    def __init__(self, config: MongoDBConfigModel) -> None:
        uri = "mongodb://{}:{}@{}:{}".format(
            quote_plus(config.username),
            quote_plus(config.password),
            config.address,
            config.port,
        )
        try:
            self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        except Exception as e:
            raise DBError(f"failed to connect: {str(e)}")

        self._projects_db = self._client[_DB_PROJECTS]

    def get_project_collection(
        self, project_id: str
    ) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self._projects_db[
            _DB_COLLECTION_PROJECT.format(projectid=project_id)
        ]  # pyright: ignore[reportUnknownVariableType]
