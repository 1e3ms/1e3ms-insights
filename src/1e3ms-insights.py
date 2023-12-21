#!/usr/bin/env python3
#
# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.logger import logger
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

from insights.api import github as github_api
from insights.error import InsightsError
from insights.logging import get_uvicorn_logging_config, setup_logging
from insights.state import GlobalState


class CustomStaticFiles(StaticFiles):
    """Add custom headers, avoid caching specific frontend files."""

    def __init__(self, static_dir: str):
        super().__init__(directory=static_dir, html=True)

    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        if scope["path"] == "/":
            response.headers.update(
                {
                    "Cache-Control": "no-cache, max-age=0, must-revalidate",
                    "Expires": "0",
                    "Pragma": "no-cache",
                }
            )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    logger.info("Starting 1e3ms-insights")

    gstate: GlobalState = app.state.gstate
    assert not gstate.inited

    try:
        await gstate.init()
        logger.info("Application global state initialized")
    except InsightsError as e:
        logger.error(f"Unable to init application: {str(e)}")
        raise BaseException()

    yield

    logger.info("Stopping 1e3ms-insights")


def get_frontend_data_path() -> str:
    """Get the path to the frontend static files."""
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "frontend",
        "dist",
    )


def insights_factory(
    static_dir: str | None = None,
) -> FastAPI:
    api_tags_meta = [{"name": "github", "description": "GitHub webhook operations"}]

    insights_app = FastAPI(
        docs_url=None,
        lifespan=lifespan,
    )
    insights_api = FastAPI(
        title="Project Insights API",
        description="Obtain insights about GitHub projects",
        version="0.1.0",
        openapi_tags=api_tags_meta,
    )

    gstate = GlobalState()
    insights_app.state.gstate = gstate
    insights_api.state.gstate = gstate

    insights_api.include_router(github_api.router)

    insights_app.mount("/api/v1", insights_api, name="API")

    if static_dir is not None:
        insights_app.mount("/", CustomStaticFiles(static_dir), name="static")

    return insights_app


def factory():
    return insights_factory(get_frontend_data_path())


async def main():
    setup_logging()
    config = uvicorn.Config(
        "1e3ms-insights:factory",
        host="0.0.0.0",
        port=8080,
        log_config=get_uvicorn_logging_config(),
        factory=True,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
