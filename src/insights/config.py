# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.


import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, field_validator


class ConfigError(Exception):
    _msg: str | None

    def __init__(self, msg: str | None = None):
        self._msg = msg

    def __str__(self) -> str:
        return f"Config Error: {self._msg}"

    def __repr__(self) -> str:
        return str(self)


class ConfigDoesNotExistError(ConfigError):
    _path: str | None

    def __init__(self, path: str | None = None):
        self._path = path

    def __str__(self) -> str:
        return self._get_str()

    def _get_str(self) -> str:
        extra_str = "" if self._path is None else f" at path '{self._path}'"
        return "Config does not exist" + extra_str

    def __repr__(self) -> str:
        return self._get_str()


class ConfigNotAFileError(ConfigError):
    _path: str | None

    def __init__(self, path: str | None = None):
        self._path = path

    def __str__(self) -> str:
        return self._get_str()

    def _get_str(self) -> str:
        extra_str = "" if self._path is None else f" at path '{self._path}'"
        return "Config is not a file" + extra_str

    def __repr__(self) -> str:
        return self._get_str()


class BadGitHubKeyFileError(ConfigError):
    _path: str | None

    def __init__(self, path: Path):
        self._path = path.as_posix()

    def __str__(self) -> str:
        return f"Bad GitHub App key file at '{self._path}'"

    def __repr__(self) -> str:
        return str(self)


class GitHubConfigModel(BaseModel):
    app_id: int
    private_key_path: Path
    webhook_secret: str

    @field_validator("private_key_path")
    @classmethod
    def key_must_exist(cls, v: Path) -> Path:
        if not v.exists() or not v.is_file():
            raise BadGitHubKeyFileError(v)
        return v


class MongoDBConfigModel(BaseModel):
    address: str
    port: int
    username: str
    password: str


class EventDBConfigModel(BaseModel):
    eventdb_path: Path
    errors_path: Path | None = Field(default=None)


class ConfigModel(BaseModel):
    github: GitHubConfigModel
    mongodb: MongoDBConfigModel
    events: EventDBConfigModel | None = Field(default=None)


class Config:
    _github: GitHubConfigModel
    _db: MongoDBConfigModel
    _eventdb: EventDBConfigModel | None

    def __init__(self, path: str) -> None:
        p = Path(path)
        if not p.exists():
            raise ConfigDoesNotExistError(path)

        if not p.is_file():
            raise ConfigNotAFileError(path)

        with p.open() as fp:
            try:
                raw = json.load(fp)
                cfg = ConfigModel.model_validate(raw)
            except json.JSONDecodeError as e:
                raise ConfigError(f"Unable to decode config JSON: {str(e)}")
            except ValidationError as e:
                raise ConfigError(f"Unable to parse config from JSON: {str(e)}")

            self._github = cfg.github
            self._db = cfg.mongodb
            self._eventdb = cfg.events

    @property
    def github(self) -> GitHubConfigModel:
        return self._github

    @property
    def db(self) -> MongoDBConfigModel:
        return self._db

    def has_eventdb(self) -> bool:
        return self._eventdb is not None

    @property
    def eventdb(self) -> Path | None:
        if self._eventdb is not None:
            return self._eventdb.eventdb_path
        return None

    @property
    def eventdb_errors(self) -> Path | None:
        if self._eventdb is not None:
            return self._eventdb.errors_path
        return None
