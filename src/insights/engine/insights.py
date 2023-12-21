# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import motor.motor_asyncio
from fastapi.logger import logger

from insights.engine.db_client import DBClient
from insights.engine.db_types import InstallationEntry
from insights.engine.installation import Installation
from insights.error import InsightsError

_DB_INSIGHTS = "insights"
_DB_INSTALLATION_BY_ID = "installation.{id}"
_COLL_INSTALLATIONS = "installations"


class Insights:
    _client: motor.motor_asyncio.AsyncIOMotorClient
    _db: motor.motor_asyncio.AsyncIOMotorDatabase
    _installations: motor.motor_asyncio.AsyncIOMotorCollection | None

    def __init__(self, db_client: DBClient) -> None:
        self._client = db_client.client
        self._db = self._client[_DB_INSIGHTS]
        self._installations = None

    async def init(self) -> None:
        try:
            await self._db.command("ping")
            logger.info("Database is available")
        except Exception as e:
            logger.error(f"Database unavailable: {str(e)}")
            raise InsightsError("Database unavailable")

        self._installations = self._db.get_collection(_COLL_INSTALLATIONS)

    async def get_installation(
        self, id: str
    ) -> motor.motor_asyncio.AsyncIOMotorDatabase:
        db_name = _DB_INSTALLATION_BY_ID.format(id=id)
        if db_name not in await self._client.list_database_names():
            await self.create_installation(id)

        return self._client[db_name]

    async def create_installation(self, id: str) -> None:
        assert self._installations is not None

        db_name = _DB_INSTALLATION_BY_ID.format(id=id)
        installation = Installation(self._client[db_name])
        await installation.init()

        installation_entry = InstallationEntry(
            installation_id=id,
        )
        new_entry = await self._installations.insert_one(
            installation_entry.model_dump(by_alias=True, exclude=set("id"))
        )
        logger.debug(f"new installation entry: {str(new_entry)}")
