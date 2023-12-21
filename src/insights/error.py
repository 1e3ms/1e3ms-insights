# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.


class InsightsError(Exception):
    _msg: str | None

    def __init__(self, msg: str | None) -> None:
        self._msg = msg

    def __str__(self) -> str:
        return f"Insights Core Error: {self._msg}"

    def __repr__(self) -> str:
        return str(self)
