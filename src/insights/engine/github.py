# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import githubkit as ghk

from insights.config import GitHubConfigModel


class InvalidPrivateKeyError(Exception):
    def __str__(self) -> str:
        return "Invalid GitHub private key"

    def __repr__(self) -> str:
        return str(self)


class Github:
    """Manages and maintains GitHub state"""

    _github: ghk.GitHub[ghk.AppAuthStrategy]

    def __init__(self, config: GitHubConfigModel) -> None:
        pvt_key = config.private_key_path.read_text()

        if len(pvt_key) == 0:
            raise InvalidPrivateKeyError()

        self._github = ghk.GitHub(
            ghk.AppAuthStrategy(config.app_id, pvt_key),
            user_agent="1e3ms-insights",
        )
        pass
