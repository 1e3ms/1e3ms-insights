#!/usr/bin/env python3
#
# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import errno
import json
import sys
from pathlib import Path
from typing import Any

import httpx

from insights.config import Config, ConfigError


def main() -> None:
    if len(sys.argv) < 3:
        print(f"usage: {sys.argv[0]} <host:port> <config.json> [event.json]")
        sys.exit(errno.EINVAL)

    addr = sys.argv[1]

    cfg_path = Path(sys.argv[2])
    if not cfg_path.exists():
        print(f"Config not found at '{cfg_path}'")
        sys.exit(errno.ENOENT)

    event_path: Path | None = None
    if len(sys.argv) == 4:
        event_path = Path(sys.argv[3])
        if not event_path.exists():
            print(f"Event file at '{event_path}' does not exist")
            sys.exit(errno.ENOENT)
        elif not event_path.is_file():
            print(f"Event file at '{event_path}' not a regular file")
            sys.exit(errno.EINVAL)

    try:
        cfg = Config(cfg_path.as_posix())
    except ConfigError as e:
        print(f"Error loading config file: {str(e)}")
        sys.exit(errno.EINVAL)

    replay_events(addr, cfg.eventdb, event_path)


def replay_events(addr: str, eventdb: Path | None, event_file: Path | None) -> None:
    if event_file is not None:
        replay_event_file(addr, event_file)
    elif eventdb is not None:
        replay_events_from_dir(addr, eventdb)
    else:
        print("No events to replay")


def replay_event_file(addr: str, event_file: Path) -> None:
    with event_file.open("r") as fp:
        try:
            event_obj = json.load(fp)
        except json.JSONDecodeError as e:
            print(f"Unable to decode event file at '{event_file}': {str(e)}")
            sys.exit(errno.EINVAL)

    if "headers" not in event_obj or "event" not in event_obj:
        print(f"Malformed event file at '{event_file}'")
        sys.exit(errno.EINVAL)

    headers: list[tuple[str, str]] = extract_headers(event_obj["headers"])
    event: dict[str, Any] = event_obj["event"]

    uri = f"http://{addr}/api/v1/github/hooks" if not addr.startswith("http") else addr

    res = httpx.post(uri, headers=headers, json=event)
    if not res.is_success:
        print(f"Error replaying event '{event_file}'")
    else:
        print(f"Success replaying event '{event_file}'")


def extract_headers(orig: list[tuple[str, str]]) -> list[tuple[str, str]]:
    headers: list[tuple[str, str]] = []
    for k, v in orig:
        if k.lower().startswith("x-github-"):
            headers.append((k, v))

    return headers


def replay_events_from_dir(addr: str, eventdb: Path) -> None:
    pass


if __name__ == "__main__":
    main()
