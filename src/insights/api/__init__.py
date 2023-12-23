# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from typing import Annotated

from fastapi import Depends, Request

from insights.engine.insights import Insights
from insights.state import GlobalState


async def gstate(request: Request) -> GlobalState:
    return request.app.state.gstate


GlobalStateDep = Annotated[GlobalState, Depends(gstate)]


async def insights(gstate: GlobalStateDep) -> Insights:
    assert gstate.inited
    assert gstate.insights is not None
    return gstate.insights


InsightsDep = Annotated[Insights, Depends(insights)]
