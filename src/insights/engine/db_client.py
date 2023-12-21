# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from urllib.parse import quote_plus

import motor.motor_asyncio
from fastapi.logger import logger

from insights.config import MongoDBConfigModel
from insights.engine.db_types import DBError


class DBClient:
    _client: motor.motor_asyncio.AsyncIOMotorClient

    def __init__(self, config: MongoDBConfigModel) -> None:
        uri = "mongodb://{}:{}@{}:{}".format(
            quote_plus(config.username),
            quote_plus(config.password),
            config.address,
            config.port,
        )
        try:
            self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
            logger.debug("MongoDB client initialized")
        except Exception as e:
            raise DBError(f"failed to connect: {str(e)}")

    @property
    def client(self) -> motor.motor_asyncio.AsyncIOMotorClient:
        return self._client
