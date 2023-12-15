# One Second Project Insights
# Copyright 2023 1e3ms contributors <code@1e3ms.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import logging.config
import os
from typing import Any

import pydash
import uvicorn.config

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    level = "INFO" if not os.getenv("INSIGHTS_DEBUG") else "DEBUG"
    log_file: str | None = os.getenv("INSIGHTS_LOG_FILE")
    _setup_logging(level, log_file)


def _setup_logging(level: str, log_file: str | None) -> None:
    handler: dict[str, Any] | None = None

    if log_file is not None:
        handler = {
            "level": level,
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "simple",
            "filename": log_file,
            "maxBytes": 10485760,
            "backupCount": 1,
        }

    cfg: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "colorized": {
                "()": "uvicorn.logging.ColourizedFormatter",
                "format": ("%(levelprefix)s %(asctime)s -- %(module)s -- %(message)s"),
                "datefmt": DATE_FORMAT,
            },
        },
        "handlers": {
            "console": {
                "level": level,
                "class": "logging.StreamHandler",
                "formatter": "colorized",
            }
        },
    }

    handlers: list[str] = ["console"]

    if handler is not None:
        cfg["handlers"]["log_file"] = handler
        handlers.append("log_file")

    cfg["root"] = {
        "level": level,
        "handlers": handlers,
    }

    logging.config.dictConfig(cfg)


def get_uvicorn_logging_config() -> dict[str, Any]:
    level = "INFO" if not os.getenv("INSIGHTS_DEBUG") else "DEBUG"
    return pydash.merge(
        uvicorn.config.LOGGING_CONFIG,
        {
            "formatters": {
                "default": {
                    "fmt": "%(levelprefix)s %(asctime)s -- %(message)s",
                    "datefmt": DATE_FORMAT,
                },
                "access": {
                    "fmt": '%(levelprefix)s %(asctime)s -- %(client_addr)s -- "%(request_line)s" %(status_code)s',  # noqa: E501
                    "datefmt": DATE_FORMAT,
                },
            },
            "handlers": {
                "default": {
                    "level": level,
                },
                "access": {"level": level},
            },
        },
    )
