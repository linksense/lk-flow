#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/30 15:12
# Copyright 2021 LinkSense Technology CO,. Ltd
import asyncio
from typing import Any, Callable, Dict, Tuple

from lk_flow import conf
from lk_flow.core import ModAbstraction
from lk_flow.env import logger


class HttpControlServer(ModAbstraction):
    """通过http接口控制server"""

    uv_task: asyncio.Task

    _default_host: str = "0.0.0.0"
    _default_port: int = 9002
    _api_path: str = "/lk_flow/api/v1"

    @classmethod
    def _get_host_port(cls, mod_config: Dict[str, Any]) -> Tuple[str, int]:
        host = mod_config.get("host", cls._default_host)
        port = mod_config.get("port", cls._default_port)
        return host, port

    @classmethod
    def setup_mod(cls, mod_config: Dict[str, Any]) -> None:
        from lk_flow.plugin.http_stuff.apis import start_server

        # get config
        host, port = cls._get_host_port(mod_config)
        log_level = mod_config.get("log_level", conf.LOG_LEVEL)
        # start FastAPI app
        loop = asyncio.get_event_loop()
        uv_task = start_server(
            host=host, port=port, log_level=log_level, api_path=cls._api_path
        )
        cls.uv_task = asyncio.create_task(uv_task)
        asyncio.ensure_future(cls.uv_task, loop=loop)

    @classmethod
    def teardown_mod(cls) -> None:
        cls.uv_task.cancel()

    @classmethod
    def get_commands(cls, mod_config: Dict[str, Any]) -> Dict[str, Callable]:
        from lk_flow.plugin.http_stuff.commands import ControlCommands

        host, port = cls._get_host_port(mod_config)
        control_command = ControlCommands(host, port, cls._api_path)
        all_command = control_command.get_all_commands()
        logger.debug(f"loading commands {all_command}")
        return all_command
