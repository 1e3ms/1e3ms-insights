# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os

from fastapi.logger import logger

from insights.config import Config, ConfigError
from insights.engine.db_client import DBClient
from insights.engine.db_types import DBError
from insights.engine.github import Github, InvalidPrivateKeyError
from insights.engine.insights import Insights
from insights.error import InsightsError


class GlobalState:
    config: Config | None
    github: Github | None
    dbc: DBClient | None
    insights: Insights | None

    inited: bool

    def __init__(self) -> None:
        self.config = None
        self.github = None
        self.dbc = None
        self.insights = None
        self.inited = False

    async def init(self) -> None:
        config_path: str | None = os.getenv("INSIGHTS_CONFIG")
        if config_path is None:
            logger.error("Unable to find config file")
            raise InsightsError("Unable to find config file")
            # sys.exit(signal.SIGILL)

        try:
            cfg = Config(config_path)
        except ConfigError as e:
            logger.error(f"Unable to obtain config: {str(e)}")
            # sys.exit(signal.SIGILL)
            raise InsightsError("Unable to obtain config")

        try:
            gh = Github(cfg.github)
            logger.debug("GitHub connection inited")
        except InvalidPrivateKeyError as e:
            logger.error(f"Unable to setup GitHub connection: {str(e)}")
            raise InsightsError("Unable to setup GitHub connection")
            # sys.exit(signal.SIGILL)

        try:
            dbc = DBClient(cfg.db)
            logger.debug("Database connection inited")
        except DBError as e:
            logger.error(f"Unable to setup database connection: {str(e)}")
            raise InsightsError("Unable to setup database")
            # sys.exit(signal.SIGILL)

        try:
            insights = Insights(cfg, gh, dbc)
            await insights.init()
        except InsightsError as e:
            logger.error(f"Unable to setup insights core: {str(e)}")
            raise InsightsError("Unable to setup insights core")
            # sys.exit(signal.SIGILL)

        self.config = cfg
        self.github = gh
        self.dbc = dbc
        self.insights = insights
        self.inited = True
